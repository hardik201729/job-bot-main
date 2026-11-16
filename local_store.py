"""
Local replacement for Google Sheets.

Stores every "sheet" (Jobs, Applications, Contacts, ...) as rows in a local
SQLite file (data/jobbot.db). It mimics the small part of the gspread API the
bot uses, so the rest of the code works unchanged:

    spreadsheet.worksheet(name) / add_worksheet(title=...)
    ws.row_values(1), ws.get_all_values(), ws.get_all_records()
    ws.append_row(row), ws.append_rows(rows), ws.update_cell(r, c, v)
    ws.find(value), ws.findall(value), ws.delete_rows(n), ws.clear()

Row/column numbers are 1-based like Google Sheets; row 1 is the header row.
The dashboard (dashboard.py) reads the same file.
"""

import json
import os
import sqlite3
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("JOBBOT_DB") or os.path.join(BASE_DIR, "data", "jobbot.db")

_lock = threading.RLock()


class WorksheetNotFound(Exception):
    pass


class Cell:
    def __init__(self, row, col, value):
        self.row = row
        self.col = col
        self.value = value

    def __repr__(self):
        return f"<Cell R{self.row}C{self.col} {self.value!r}>"


def _connect(path=DB_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""CREATE TABLE IF NOT EXISTS sheets (
                        name TEXT PRIMARY KEY,
                        created_order INTEGER)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS rows (
                        sheet TEXT NOT NULL,
                        pos   INTEGER NOT NULL,
                        cells TEXT NOT NULL,
                        PRIMARY KEY (sheet, pos))""")
    conn.commit()
    return conn


def _to_str(v):
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v)) if abs(v) < 1e15 else str(v)
    return str(v)


def _numericise(v):
    """Same idea as gspread's get_all_records: '12' -> 12, '8.5' -> 8.5."""
    if v == "" or not isinstance(v, str):
        return v
    try:
        return int(v)
    except ValueError:
        pass
    try:
        f = float(v)
        if f != f or f in (float("inf"), float("-inf")):
            return v
        return f
    except ValueError:
        return v


class Worksheet:
    def __init__(self, store, title):
        self._store = store
        self.title = title

    @property
    def _conn(self):
        return self._store.conn

    # ---------- reads ----------
    def get_all_values(self):
        with _lock:
            cur = self._conn.execute(
                "SELECT cells FROM rows WHERE sheet=? ORDER BY pos", (self.title,))
            return [json.loads(r[0]) for r in cur.fetchall()]

    def row_values(self, row):
        with _lock:
            cur = self._conn.execute(
                "SELECT cells FROM rows WHERE sheet=? AND pos=?", (self.title, row))
            r = cur.fetchone()
            if not r:
                return []
            vals = json.loads(r[0])
            while vals and vals[-1] == "":
                vals.pop()
            return vals

    def get_all_records(self, head=1, **_kwargs):
        values = self.get_all_values()
        if len(values) < head:
            return []
        headers = values[head - 1]
        records = []
        for row in values[head:]:
            row = list(row) + [""] * (len(headers) - len(row))
            records.append({h: _numericise(row[i]) for i, h in enumerate(headers)})
        return records

    def find(self, query, **_kwargs):
        query = _to_str(query)
        for r_idx, row in enumerate(self.get_all_values(), start=1):
            for c_idx, v in enumerate(row, start=1):
                if v == query:
                    return Cell(r_idx, c_idx, v)
        return None

    def findall(self, query, **_kwargs):
        query = _to_str(query)
        out = []
        for r_idx, row in enumerate(self.get_all_values(), start=1):
            for c_idx, v in enumerate(row, start=1):
                if v == query:
                    out.append(Cell(r_idx, c_idx, v))
        return out

    # ---------- writes ----------
    def _next_pos(self):
        cur = self._conn.execute(
            "SELECT COALESCE(MAX(pos), 0) FROM rows WHERE sheet=?", (self.title,))
        return cur.fetchone()[0] + 1

    def append_row(self, values, **_kwargs):
        self.append_rows([values])

    def append_rows(self, rows, **_kwargs):
        with _lock:
            pos = self._next_pos()
            self._conn.executemany(
                "INSERT INTO rows (sheet, pos, cells) VALUES (?, ?, ?)",
                [(self.title, pos + i, json.dumps([_to_str(v) for v in row]))
                 for i, row in enumerate(rows)])
            self._conn.commit()

    def update_cell(self, row, col, value):
        with _lock:
            cur = self._conn.execute(
                "SELECT cells FROM rows WHERE sheet=? AND pos=?", (self.title, row))
            r = cur.fetchone()
            if r:
                vals = json.loads(r[0])
            else:
                # Fill any gap so positions stay contiguous
                last = self._next_pos()
                for p in range(last, row):
                    self._conn.execute(
                        "INSERT INTO rows (sheet, pos, cells) VALUES (?, ?, '[]')",
                        (self.title, p))
                vals = []
            while len(vals) < col:
                vals.append("")
            vals[col - 1] = _to_str(value)
            self._conn.execute(
                "INSERT OR REPLACE INTO rows (sheet, pos, cells) VALUES (?, ?, ?)",
                (self.title, row, json.dumps(vals)))
            self._conn.commit()

    def update(self, *args, **kwargs):
        raise NotImplementedError("Worksheet.update is not supported by local_store")

    def delete_rows(self, start_index, end_index=None):
        end_index = end_index or start_index
        n = end_index - start_index + 1
        with _lock:
            c = self._conn
            c.execute("DELETE FROM rows WHERE sheet=? AND pos BETWEEN ? AND ?",
                      (self.title, start_index, end_index))
            # Shift following rows up (two steps to avoid primary-key clashes)
            c.execute("UPDATE rows SET pos = -(pos - ?) WHERE sheet=? AND pos > ?",
                      (n, self.title, end_index))
            c.execute("UPDATE rows SET pos = -pos WHERE sheet=? AND pos < 0", (self.title,))
            c.commit()

    def delete_row(self, index):
        self.delete_rows(index)

    def clear(self):
        with _lock:
            self._conn.execute("DELETE FROM rows WHERE sheet=?", (self.title,))
            self._conn.commit()


class LocalSpreadsheet:
    def __init__(self, path=DB_PATH):
        self.path = path
        self.conn = _connect(path)

    def worksheet(self, title):
        with _lock:
            cur = self.conn.execute("SELECT 1 FROM sheets WHERE name=?", (title,))
            if not cur.fetchone():
                raise WorksheetNotFound(title)
        return Worksheet(self, title)

    def add_worksheet(self, title, rows=None, cols=None, **_kwargs):
        with _lock:
            cur = self.conn.execute("SELECT COALESCE(MAX(created_order), 0) FROM sheets")
            order = cur.fetchone()[0] + 1
            self.conn.execute("INSERT OR IGNORE INTO sheets (name, created_order) VALUES (?, ?)",
                              (title, order))
            self.conn.commit()
        return Worksheet(self, title)

    def worksheets(self):
        cur = self.conn.execute("SELECT name FROM sheets ORDER BY created_order")
        return [Worksheet(self, r[0]) for r in cur.fetchall()]


def open_spreadsheet(path=DB_PATH):
    return LocalSpreadsheet(path)


def export_all(path=DB_PATH):
    """Return {sheet_name: {"headers": [...], "rows": [[...], ...]}} for the dashboard."""
    store = LocalSpreadsheet(path)
    out = {}
    for ws in store.worksheets():
        values = ws.get_all_values()
        headers = values[0] if values else []
        out[ws.title] = {"headers": headers, "rows": values[1:]}
    store.conn.close()
    return out
