"""Public Chapter 9 tutorial SQL shared by book figures and slides.

These definitions never open a database. Run authoring examples against a
read-only connection; save views only in a separate student working copy.
"""

HEADER = (
    "/* Chapter 9: manufacturing variance, first look\n"
    "   Database: CharlesRiver_Work.sqlite (a copy of CharlesRiver.sqlite)\n"
    "   Prepared by: your name, date\n"
    "   Checks: every close adds up; the 2026 postings exclude JE-2026-000296 */"
)

QUERIES = [
    ("all_accounts", "-- Tutorial 9.1: every column of the chart of accounts",
     "SELECT *\n"
     "FROM Account;"),
    ("account_columns", "-- Tutorial 9.1: the columns that identify each account",
     "SELECT AccountID, AccountNumber, AccountName,\n"
     "    AccountType, AccountSubType\n"
     "FROM Account;"),
    ("variance_check", "-- Tutorial 9.1: the parts of each variance and their check",
     "SELECT WorkOrderCloseID, CloseDate,\n"
     "    MaterialVarianceAmount AS Material,\n"
     "    ConversionVarianceAmount AS Conversion,\n"
     "    TotalVarianceAmount AS Total,\n"
     "    ROUND(MaterialVarianceAmount + ConversionVarianceAmount\n"
     "        - TotalVarianceAmount, 2) AS CheckDifference\n"
     "FROM WorkOrderClose;"),
    ("accounts_by_number", "-- Tutorial 9.2: the two manufacturing accounts by number",
     "SELECT AccountID, AccountNumber, AccountName\n"
     "FROM Account\n"
     "WHERE AccountNumber IN (1090, 5080);"),
    ("variance_postings", "-- Tutorial 9.2: the variance postings of fiscal 2026",
     "SELECT GLEntryID, PostingDate, Debit, Credit,\n"
     "    SourceDocumentType, VoucherNumber, Description\n"
     "FROM GLEntry\n"
     "WHERE AccountID = 93 AND FiscalYear = 2026;"),
    ("source_types", "-- Tutorial 9.2: the source document types of those postings",
     "SELECT DISTINCT SourceDocumentType\n"
     "FROM GLEntry\n"
     "WHERE AccountID = 93 AND FiscalYear = 2026;"),
    ("closing_entry", "-- Tutorial 9.2: the closing entry, left out of any analysis",
     "SELECT GLEntryID, PostingDate, Debit, Credit,\n"
     "    VoucherNumber, Description\n"
     "FROM GLEntry\n"
     "WHERE AccountID = 93 AND FiscalYear = 2026\n"
     "    AND SourceDocumentType = 'JournalEntry';"),
    ("check_failures", "-- Tutorial 9.2: closes whose parts differ from their total",
     "SELECT WorkOrderCloseID, TotalVarianceAmount\n"
     "FROM WorkOrderClose\n"
     "WHERE ROUND(MaterialVarianceAmount + ConversionVarianceAmount\n"
     "    - TotalVarianceAmount, 2) <> 0;"),
    ("open_work_orders", "-- Tutorial 9.2: work orders not yet closed",
     "SELECT WorkOrderNumber, Status, ReleasedDate, DueDate,\n"
     "    COALESCE(CompletedDate, 'not completed') AS Completed,\n"
     "    CAST(SUBSTR(WorkOrderNumber, 4, 4) AS INTEGER) AS ReleaseYear\n"
     "FROM WorkOrder\n"
     "WHERE ClosedDate IS NULL;"),
    ("top_ten", "-- Tutorial 9.3: the ten largest variances of fiscal 2026",
     "SELECT WorkOrderCloseID, WorkOrderID, CloseDate,\n"
     "    MaterialVarianceAmount AS Material,\n"
     "    DirectLaborVarianceAmount AS Labor,\n"
     "    OverheadVarianceAmount AS Overhead,\n"
     "    TotalVarianceAmount AS Total,\n"
     "    ROUND(OverheadVarianceAmount / TotalVarianceAmount, 2)\n"
     "        AS OverheadShare\n"
     "FROM WorkOrderClose\n"
     "WHERE CloseDate BETWEEN '2026-01-01' AND '2026-12-31'\n"
     "ORDER BY TotalVarianceAmount DESC\n"
     "LIMIT 10;"),
    ("review_threshold", "-- Tutorial 9.3: closes of 2026 above $1,000 either way",
     "SELECT WorkOrderCloseID, CloseDate, TotalVarianceAmount\n"
     "FROM WorkOrderClose\n"
     "WHERE CloseDate BETWEEN '2026-01-01' AND '2026-12-31'\n"
     "    AND ABS(TotalVarianceAmount) > 1000\n"
     "ORDER BY TotalVarianceAmount;"),
]
