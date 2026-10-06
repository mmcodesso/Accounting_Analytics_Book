# Can the dataset roll to a new window? (Phase 2 memo, 2026-10-02)

**Question.** If the generator produces fiscal 2025–2027 instead of 2024–2026, do the conditions the book's storylines rely on still hold?

**Answer: yes, with the same seed and a pinned environment.** The roll is feasible after small changes to the generator.

- With the seed unchanged, every storyline of the contract holds on the rolled data, and the magnitudes stay close to the 2026 edition's. One detail of the start-up year did not hold, and the text was loosened (decision 3).
- **Final state:** with the generator's branch code in the pinned environment (decision 2):
  - fiscal 2024–2026 rebuilds release v2026.1 table for table (83 of 83);
  - fiscal 2025–2027 with the same seed passes all 33 checks of the contract.

The sections below record how the work got there.

## What was done

1. **Year anchor in the generator** (branch `book-roll-feasibility` of greenfield_database; not committed). Five calibrations were tied to the years 2024–2026:
   - the plant's load uplift and its bridge year (`planning.py`);
   - cost growth (`journals.py`);
   - pay growth (`payroll.py`);
   - the capital plan's dates (`config/capex_plan.yaml`, through `fixed_assets.py`).

   A new `scenario.py` states them relative to the scenario's end year. That year is the year of `fiscal_year_end` unless `scenario_end_year` is set. The perf and reconciliation configs, whose windows end in 2027 and 2030, pin it to 2026, so every existing build is unchanged.
2. **Exact-rebuild test.** The same settings were run with the current code (run A) and with the anchored code (run B) in the same environment: **83 of 83 tables are identical**, so the change is behavior-neutral.
3. **Data contract v0** (`facts/contract.py`): 33 checks of the storylines, quirks and schema, written relative to the window. **33 of 33 pass on v2026.1.**
4. **Dry runs.** Fiscal 2025–2027 with three seeds, compared below with v2026.1.

## Results

| Check | v2026.1 | Same seed (20260401) | Seed 20270401 | Seed 7 |
|---|---|---|---|---|
| Schema, window, time-record cut-off, three-pay-date months, no wage accrual (S1, W1–W4) | pass | pass | pass | pass |
| Q4 Furniture margin falls (P1) | 43.3% → 41.1% | 43.0% → 40.7% | 41.6% → 39.4% | 42.5% → 40.4% |
| Price effect: price, units, cost per unit (P2) | −3.4%, +0.4%, −0.9% | −4.9%, −10.6%, −1.8% | −4.5%, +2.1%, −1.3% | −3.7%, −3.2%, −0.8% |
| Promotion calendar, Furniture promotion leads (P3) | 576 lines | 573 | 583 | 533 |
| Budget volume inflated (P6) | 3.48× | 3.47× | 3.44× | 3.34× |
| Manufacturing variance growth F→C (M1) | +71.9% | +66.9% | +66.3% | **+32.4% (fails)** |
| Surge days by year (M2) | 12, 32, 49 | 4, 38, 53 | 11, 31, 37 | 11, 16, 30 |
| Direct overtime share (M3) | .128, .220, .270 | .127, .231, .283 | .141, .232, .254 | .145, .174, .226 |
| Start-up build: indirect hours a month, Feb–May vs Jul–Dec of F (M5) | 62 vs 2,629 | **556 vs 2,734 (fails)** | **590 vs 3,225 (fails)** | **418 vs 2,972 (fails)** |
| Sales tax never remitted (C1) | pass | pass | pass | pass |
| Cash falls while net income is positive (C2) | −0.94M | −1.21M | −0.85M | **+2.56M (fails)** |
| Checks passing (contract) | 33 | 31 | 31 | 29 |

All four runs here also fail P7 (same-name customers), including run A on the 2024–2026 window. That failure comes from the environment (finding 2), not from the roll.

## Findings

1. **The year anchor works.** A rolled window shifts the calibration, the bridge year, cost and pay growth, and the capital plan by one year. Builds that end in 2026 are identical.
2. **v2026.1 could not be rebuilt in the system Python** (resolved: see decision 2). Run A differs from v2026.1 in 5 tables, for two environment reasons:
   - **Faker is not installed** in any Python here. The generator falls back to placeholder names ("Counterparty 404 Partners", "Employee 402"), and the same-name customers the book uses (two Brown LLCs) disappear.
   - **pandas behaves differently.** The duplicate-payment anomaly copies `CheckNumber or PaymentNumber`. In v2026.1's build environment, a missing check number was evidently NaN, which counts as true, so four of the six planted duplicates kept no check number (the "generator bug" the book relies on). Under pandas 2.2.3 here it is `None`, so all six get one.

   The requirements are not pinned, and the build environment is not recorded.
3. **The seed must stay fixed.** With the same seed, magnitudes stay close to the 2026 edition's. Seed 7 weakens the manufacturing variance growth and turns the cash story around, and seed 20270401 shifts the surge days.
4. **The start-up build survives, but not its "almost no indirect time" detail.** February–May of the first year still show high direct hours, high output and many work orders released. Indirect time there is about a fifth of the later level instead of almost none. The likely cause is the calendar: 1 January 2024 was a Monday, and 1 January 2025 a Wednesday.
5. **Calendar details move, as expected.**
   - The time records end on 12-14 instead of 12-11, and the open pay periods start 12-15 and 12-29.
   - The first year has fewer surge days (4 instead of 12).
   - The traced documents and IDs change.

   The facts registry (Phase 3) handles these.
6. **Every exact value changes a little**, for example the Q4 margin (40.7% instead of 41.1%) and promotion 8's lines (573 instead of 576). This confirms that the hidden notes must be generated from the registry.

## Decisions (author, 2026-10-02)

1. **Seed: fixed.** Every roll keeps `random_seed: 20260401` and changes only the window.
2. **Environment: recreated and pinned.** A virtual environment holds the package versions current on the build date (2026-05-08): Python 3.13, pandas 3.0.2, numpy 2.4.4, Faker 40.15.0, PyYAML 6.0.3, openpyxl 3.1.5, XlsxWriter 3.2.9.
   - **First rebuild:** it reproduced v2026.1 in 82 of 83 tables. Customer.CustomerSince differed, because Faker draws it relative to the day the build runs (`date_between("-10y", "-1y")`).
   - **Fix:** the draw is now relative to a fixed reference date, 2026-05-08, the day v2026.1 was built, moved with the scenario (`scenario.reference_date()`).
   - **Second rebuild:** 83 of 83 tables are identical to v2026.1.
   - **Pinned:** the versions are in the generator's `requirements-lock.txt`, and `docs/technical/dataset-delivery.md` says to build releases with it.
   - **Logging:** each build now records its Python and package versions and the scenario end year (`main.py`, `environment_versions()`).
   - **The rolled build** in this environment (fiscal 2025–2027, seed 20260401) passes 33 of 33 checks. With real names, the same-name customers are back. One check number repeats instead of two, because the planted pairs fall on different payments.
3. **Start-up detail: loosen the text.** Chapters 11 and 12 now say the start-up months have far less (or little) indirect time than later in the year, and that most of their hours were direct. Contract M5 tests a ratio below 0.30, so it passes on v2026.1 (0.02) and on all three dry runs (0.14–0.20).
4. **Check-number quirk: keep v2026.1's behavior, deterministically.** The duplicate-payment anomaly takes a check payment's number as the shared reference, and leaves an ACH or wire pair without one under any pandas version (`anomalies.py`).
5. **Still open:** committing the generator branch, after its test suite runs.
