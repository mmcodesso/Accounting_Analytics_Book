"""Drive Excel through COM to build the Part II companion workbooks.

Every build runs in its own hidden Excel instance (DispatchEx), never in an Excel window the author has open, and
quits it afterwards. Nothing simulates a click or a keystroke: the builder calls Excel's object model, the same calls
the interface makes when a reader follows a tutorial.

Power Query queries are added as M text (Workbook.Queries) whose step names match those the Power Query Editor gives
the reader's own steps (Source, Navigation, Changed Type, Filtered Rows, ...), and each query is loaded as an Excel
Table through the Mashup OLE DB provider, as Close & Load does.
"""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from pathlib import Path

import pythoncom
import win32com.client as wc

# Excel constants (the subset the builders use)
XL_SRC_EXTERNAL, XL_SRC_QUERY, XL_YES, XL_CMD_SQL = 0, 3, 1, 2
XL_OPENXML_WORKBOOK = 51
XL_ROW, XL_COLUMN, XL_PAGE, XL_DATA = 1, 2, 3, 4
XL_SUM, XL_COUNT = -4157, -4112
XL_ASCENDING, XL_DESCENDING = 1, 2
XL_EXPRESSION = 2
XL_VALIDATE_DECIMAL, XL_VALID_ALERT_STOP, XL_BETWEEN = 2, 1, 1
XL_COLUMN_CLUSTERED, XL_LINE_MARKERS, XL_WATERFALL, XL_XY_SCATTER = 51, 65, 119, -4169
XL_PERCENT_DIFFERENCE_FROM, XL_PERCENT_OF_COLUMN, XL_NORMAL = 4, 7, -4143
XL_DATABASE = 1
BLUE = 0xFF0000                          # RGB(0, 0, 255): Excel stores colors as BGR integers
LIGHT_FILL = 0xE7F2FE                    # #FEF2E7, a light amber tint, as BGR


BUSY = (-2147418111, -2147417846)       # RPC_E_CALL_REJECTED, RPC_E_SERVERCALL_RETRYLATER: Excel is busy


def retry(fn, *args, timeout: float = 600.0):
    """Call fn, retrying while Excel rejects the call because it is busy (saving or calculating)."""
    deadline = time.time() + timeout
    while True:
        try:
            return fn(*args)
        except pythoncom.com_error as exc:
            if exc.hresult not in BUSY or time.time() > deadline:
                raise
            time.sleep(0.25)


def wait_ready(app, timeout: float = 600.0) -> None:
    """Wait until Excel is ready and has finished calculating."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if app.Ready and app.CalculationState == 0:        # xlDone
                return
        except pythoncom.com_error as exc:
            if exc.hresult not in BUSY:
                raise
        time.sleep(0.25)
    raise TimeoutError("Excel stayed busy")


LOCK_FILE = Path(os.environ.get("TEMP", ".")) / "accounting-analytics-excel.lock"


def _acquire_excel_lock(timeout: float = 4 * 3600):
    """One Excel build at a time on this machine: concurrent hidden instances made Excel unstable."""
    import msvcrt
    fh = open(LOCK_FILE, "a+b")
    deadline = time.time() + timeout
    while True:
        try:
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            return fh
        except OSError:
            if time.time() > deadline:
                fh.close()
                raise TimeoutError("another Excel build held the lock for too long")
            time.sleep(2)


def _release_excel_lock(fh) -> None:
    import msvcrt
    try:
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
    finally:
        fh.close()


@contextmanager
def excel():
    """A hidden Excel instance of its own, closed even when the build fails.

    COM is initialized once per thread and left initialized: uninitializing and initializing again between instances
    made the next instance fail with an RPC error. After Quit, the builder waits for this instance's process (and only
    this one, by its process ID) to exit, and ends it if it hangs, so no hidden Excel is left running."""
    import win32api
    import win32con
    import win32event
    import win32process
    lock = _acquire_excel_lock()
    pythoncom.CoInitialize()
    app = wc.DispatchEx("Excel.Application")
    pid = win32process.GetWindowThreadProcessId(app.Hwnd)[1]
    app.Visible = False
    app.DisplayAlerts = False
    app.ScreenUpdating = False
    app.AskToUpdateLinks = False
    try:
        yield app
    finally:
        try:
            for wb in list(app.Workbooks):
                wb.Close(False)
            app.Quit()
        except pythoncom.com_error:
            pass                                    # the instance already died; its process is ended below
        del app
        try:
            handle = win32api.OpenProcess(win32con.SYNCHRONIZE | win32con.PROCESS_TERMINATE, False, pid)
        except win32api.error:
            handle = None                           # already gone
        if handle:
            if win32event.WaitForSingleObject(handle, 30_000) != win32event.WAIT_OBJECT_0:
                win32api.TerminateProcess(handle, 1)
            win32api.CloseHandle(handle)
        _release_excel_lock(lock)


def add_query(wb, name: str, m: str, description: str = ""):
    return wb.Queries.Add(name, m, description)


def load_query(wb, name: str, sheet_name: str, after=None):
    """Load a query to a new worksheet as an Excel Table named after the query, as Close & Load does."""
    ws = add_sheet(wb, after=after)
    ws.Name = sheet_name
    connection = (f"OLEDB;Provider=Microsoft.Mashup.OleDb.1;Data Source=$Workbook$;Location={name};"
                  "Extended Properties=\"\"")
    lo = ws.ListObjects.Add(XL_SRC_EXTERNAL, connection, None, XL_YES, ws.Range("$A$1"))
    qt = lo.QueryTable
    qt.CommandType = XL_CMD_SQL
    qt.CommandText = [f"SELECT * FROM [{name}]"]
    qt.RowNumbers = False
    qt.FillAdjacentFormulas = False
    qt.PreserveFormatting = True
    qt.RefreshOnFileOpen = False
    qt.BackgroundQuery = False
    qt.AdjustColumnWidth = True
    qt.PreserveColumnInfo = True
    qt.Refresh(False)
    lo.Name = name
    conn = qt.WorkbookConnection
    conn.Name = f"Query - {name}"
    conn.Description = f"Connection to the '{name}' query in the workbook."
    return lo


def refresh_all(wb) -> float:
    """Refresh every query Table and then every PivotTable, synchronously (Data > Refresh All, waited for). Each call
    waits until Excel is ready and is retried while Excel rejects it as busy (after a query's M text changes, for
    example)."""
    start = time.time()
    app = wb.Application
    wait_ready(app)
    tables = retry(lambda: [lo for ws in wb.Worksheets for lo in ws.ListObjects
                            if lo.SourceType in (XL_SRC_EXTERNAL, XL_SRC_QUERY)])   # Power Query Tables: xlSrcQuery
    for lo in tables:
        retry(lambda t=lo: t.QueryTable.Refresh(False))
        wait_ready(app)
    pivots = retry(lambda: [pt for ws in wb.Worksheets for pt in ws.PivotTables()])
    for pt in pivots:
        retry(lambda p=pt: p.PivotCache().Refresh())
        wait_ready(app)
    retry(app.CalculateFull)
    wait_ready(app)
    return time.time() - start


def add_column(lo, name: str, formula: str, number_format: str | None = None):
    """A calculated column: a header to the right of the Table and one formula that fills every row."""
    col = lo.ListColumns.Add()
    col.Name = name
    col.DataBodyRange.Formula2 = formula
    if number_format:
        col.DataBodyRange.NumberFormat = number_format
    return col


def table(wb, name: str):
    for ws in wb.Worksheets:
        for lo in ws.ListObjects:
            if lo.Name == name:
                return lo
    raise KeyError(f"no Table named {name}")


def name_cell(wb, name: str, ref: str):
    wb.Names.Add(Name=name, RefersTo=f"={ref}")


def put(ws, cells: dict[str, object], formulas: bool = False):
    """Values (or formulas) into cells by address."""
    for addr, value in cells.items():
        if formulas and isinstance(value, str) and value.startswith("="):
            ws.Range(addr).Formula2 = value
        else:
            ws.Range(addr).Value = value


def add_sheet(wb, after=None, before=None):
    """A new worksheet before or after a given one (by default, last). Late-bound COM ignores the After keyword and
    adds the sheet before the active one, so the arguments go by position, with None for Before."""
    if before is not None:
        return wb.Worksheets.Add(before)
    return wb.Worksheets.Add(None, after if after is not None else wb.Worksheets(wb.Worksheets.Count))


def sheet(wb, name: str, after=None, before=None):
    ws = add_sheet(wb, after=after, before=before)
    ws.Name = name
    return ws


def repoint(wb, old: str, new: str) -> int:
    """Change the source path of every query (Data Source Settings > Change Source, done in the M text)."""
    wait_ready(wb.Application)

    def run() -> int:
        changed = 0
        for q in wb.Queries:
            if old in q.Formula:
                q.Formula = q.Formula.replace(old, new)
                changed += 1
        return changed
    return retry(run)


def save_copy(wb, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    wait_ready(wb.Application)
    retry(wb.SaveCopyAs, str(path))
    wait_ready(wb.Application)
