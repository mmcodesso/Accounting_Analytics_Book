"""Chapter 2's instructor notes: the values each note states, and the claims its wording makes."""

from __future__ import annotations

from collections import Counter

from notes import note

EXERCISES = "chapters/02-understanding-data/_exercises.qmd"
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]
ANOMALY_LOG_REFERENCES = 6      # duplicate payment references in the generator's AnomalyLog (outside the database)


def and_join(items) -> str:
    items = [str(i) for i in items]
    return items[0] if len(items) == 1 else (" and ".join(items) if len(items) == 2
                                             else ", ".join(items[:-1]) + ", and " + items[-1])


@note("ch02.ex6", EXERCISES)
def ex6(d, claim):
    # (2) SupplierID and InvoiceNumber that appear more than once in PurchaseInvoice
    invoices = d.q(
        "SELECT p.SupplierID, p.InvoiceNumber, p.PurchaseInvoiceID, p.InvoiceDate, p.GrandTotal, "
        "(SELECT COUNT(*) FROM DisbursementPayment x WHERE x.PurchaseInvoiceID = p.PurchaseInvoiceID) "
        "FROM PurchaseInvoice p JOIN (SELECT SupplierID, InvoiceNumber FROM PurchaseInvoice GROUP BY 1, 2 "
        "HAVING COUNT(*) > 1) k USING (SupplierID, InvoiceNumber) ORDER BY 1, 2, 3")
    pairs: dict[tuple, list] = {}
    for r in invoices:
        pairs.setdefault((r[0], r[1]), []).append(r)
    claim(all(len(p) == 2 for p in pairs.values()), "each duplicated supplier invoice number appears exactly twice")
    suppliers = sorted({s for s, _ in pairs})
    claim(len(suppliers) > 1, "more than one supplier has a duplicated invoice number (the wording says suppliers)")
    per_year = Counter((s, int(p[0][3][:4])) for (s, _), p in pairs.items())
    claim(all(int(p[0][3][:4]) == int(p[1][3][:4]) for p in pairs.values())
          and set(per_year) == {(s, y) for s in suppliers for y in d.years} and set(per_year.values()) == {1},
          "each of those suppliers has one pair in each fiscal year")
    claim(all(p[0][3] != p[1][3] for p in pairs.values()), "the two invoices of each pair have different dates")
    claim(all(p[0][4] != p[1][4] for p in pairs.values()), "the two invoices of each pair have different amounts")
    claim(all(r[5] == 1 for r in invoices), "each invoice of the pairs was paid once")
    example = max(invoices, key=lambda r: r[4])[1]          # the pair with the largest invoice

    # (2) SupplierID and CheckNumber that appear more than once in DisbursementPayment
    checks = d.q(
        "SELECT p.SupplierID, p.CheckNumber, p.DisbursementID, p.PurchaseInvoiceID, p.Amount, i.GrandTotal "
        "FROM DisbursementPayment p JOIN PurchaseInvoice i ON i.PurchaseInvoiceID = p.PurchaseInvoiceID "
        "JOIN (SELECT SupplierID, CheckNumber FROM DisbursementPayment WHERE CheckNumber IS NOT NULL "
        "GROUP BY 1, 2 HAVING COUNT(*) > 1) k USING (SupplierID, CheckNumber) ORDER BY 2, 3")
    by_check: dict[str, list] = {}
    for r in checks:
        by_check.setdefault(r[1], []).append(r)
    claim(len(by_check) > 1, "more than one check number repeats (the wording is plural: check numbers, each pair)")
    claim(all(len(p) == 2 for p in by_check.values()), "each repeated check number is on exactly two payments")
    check_suppliers = sorted({r[0] for r in checks})
    claim(len(check_suppliers) == 1, "the repeated check numbers all belong to one supplier")
    claim(all(p[0][3] != p[1][3] and p[0][4] != p[1][4] and p[0][5] != p[1][5] for p in by_check.values()),
          "each pair of payments pays two different invoices of different amounts")
    claim(len(by_check) < ANOMALY_LOG_REFERENCES,
          "fewer repeated check numbers are in the data than the AnomalyLog's six references")

    # (4) payments against each invoice's GrandTotal
    paid = d.q("SELECT i.GrandTotal, p.s, p.n FROM PurchaseInvoice i JOIN (SELECT PurchaseInvoiceID, SUM(Amount) AS s, "
               "COUNT(*) AS n FROM DisbursementPayment GROUP BY 1) p ON p.PurchaseInvoiceID = i.PurchaseInvoiceID")
    claim(not any(s > total + 0.005 for total, s, _ in paid), "no invoice is paid above its GrandTotal")
    installments = sum(1 for _, _, n in paid if n > 1)

    return dict(invoice_numbers=WORDS[len(pairs)], suppliers=and_join(suppliers), example=example,
                checks=WORDS[len(by_check)], check_supplier=check_suppliers[0],
                check_pairs=[(c, [r[2] for r in p]) for c, p in by_check.items()], installments=installments)
