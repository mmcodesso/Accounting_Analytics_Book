"""Read-only access to a Charles River database, with its fiscal window.

F, P, and C are the first, prior, and current fiscal years of the window (C is the last year with
sales invoices posted), and N = C + 1. The data contract and the note templates use these names, so
nothing that reads the data names a fixed year.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from paths import DB  # noqa: E402


class Data:
    def __init__(self, path: Path = DB):
        self.path = Path(path)
        self.con = sqlite3.connect(f"{self.path.resolve().as_uri()}?mode=ro", uri=True)
        self.F = self.one("SELECT MIN(FiscalYear) FROM GLEntry")
        self.C = self.one("SELECT MAX(FiscalYear) FROM GLEntry WHERE SourceDocumentType = 'SalesInvoice'")
        self.P, self.N = self.C - 1, self.C + 1
        self.years = list(range(self.F, self.C + 1))
        self.closes = [r[0] for r in self.q("SELECT EntryNumber FROM JournalEntry WHERE EntryType LIKE 'Year-End Close%' "
                                            "ORDER BY PostingDate, EntryNumber")]

    def q(self, sql: str, *args):
        return self.con.execute(sql, args).fetchall()

    def one(self, sql: str, *args):
        return self.con.execute(sql, args).fetchone()[0]

    def account(self, number: str) -> int:
        account_id = self.one("SELECT AccountID FROM Account WHERE AccountNumber = ?", number)
        if account_id is None:
            raise LookupError(f"no account {number}")
        return account_id

    def balance(self, numbers: list[str], through: str) -> float:
        ids = ",".join(str(self.account(n)) for n in numbers)
        return self.one(f"SELECT COALESCE(SUM(Debit) - SUM(Credit), 0) FROM GLEntry "
                        f"WHERE AccountID IN ({ids}) AND PostingDate <= ?", through) or 0.0

    def no_closes(self) -> str:
        return "VoucherNumber NOT IN (" + ",".join(f"'{e}'" for e in self.closes) + ")"

    def anomalies(self, kind: str) -> list[int] | None:
        """The primary keys the generator's AnomalyLog lists for one anomaly type, read once from the
        support workbook beside the database (read-only); None if there is no support workbook."""
        if not hasattr(self, "_anomaly_log"):
            self._anomaly_log = None
            path = self.path.parent / "CharlesRiver_support.xlsx"
            if path.is_file():
                import openpyxl
                wb = openpyxl.load_workbook(path, read_only=True)
                try:
                    rows = list(wb["AnomalyLog"].iter_rows(values_only=True))
                finally:
                    wb.close()
                t, k = rows[0].index("anomaly_type"), rows[0].index("primary_key_value")
                self._anomaly_log = [(r[t], int(r[k])) for r in rows[1:] if r and r[t] is not None]
        if self._anomaly_log is None:
            return None
        return sorted(key for t, key in self._anomaly_log if t == kind)

    def closes_of(self, year: int) -> list[str]:
        """The year-end close entries dated at the end of a fiscal year, in posting order."""
        return [r[0] for r in self.q("SELECT EntryNumber FROM JournalEntry WHERE EntryType LIKE 'Year-End Close%' "
                                     "AND PostingDate = ? ORDER BY EntryNumber", f"{year}-12-31")]
