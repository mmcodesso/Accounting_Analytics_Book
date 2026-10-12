# Reference models

These Power BI projects are the verification models written while Part IV, its case and Chapter 18 were drafted, by the
`make_*.py` scripts one folder up: CR14 to CR16 (the reporting package of Chapters 14 to 16), AM16 (Audit
Monitoring), CC4 (the Part IV case) and CR18 (Chapter 18). Each was opened in Power BI Desktop and refreshed, and the
DAX of its chapter ran against it through ADOMD.NET (`scripts/verify/dax_check.ps1`).

They are checking tools, not companion files. Readers receive the projects that `scripts/companion/pbibuild` builds,
and where the two differ, the builders are the source of truth. The models keep some drafting history that the
shipped files do not have: AM16 still holds the CostCenterReview table of an early draft of Tutorial 16.3, and CR16
holds the Security table and the roles of the appendix on publishing and security, with four test roles that use
fixed sign-in names, while the shipped package gains the table and its two roles only in Tutorial B.1. The models
are updated only where a DAX check of the text needs them, as for the KEEPFILTERS of Chapter 15's plant hours; the
Checks query that every build runs in Desktop is what verifies the shipped files.
