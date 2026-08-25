# Open Payments — the GLP-1 marketing war has a public ledger

Every payment from every pharma company to every U.S. clinician is disclosed by
law (Sunshine Act) and published by CMS. This repo rebuilds the commercial
playbooks of the GLP-1 category (Novo Nordisk vs. Eli Lilly) from that ledger:
~15-17M records per year, 2021-2025.

**Status: in progress.** Findings will be published as they survive their checks.

## Method

- **What's data and what's my call**: every analytical choice is logged in
  [`decisions.md`](decisions.md) before it is implemented, with rejected
  alternatives and what would invalidate it.
- **Reconciliation first**: no number is published before totals close against
  CMS official aggregates (`findings/checks.md`).
- **Kill-tests**: every finding is attacked before publication (data artifacts,
  sensitivity to my own rules, alternative explanations). Survival is earned by
  tests, not arguments.
- **Regenerable = auditable**: nothing is typed by hand. Raw data is not
  committed; `scripts/01_descargar.py` + checksums reproduce it.

## Reproduce

```bash
uv sync
uv run scripts/01_descargar.py
uv run scripts/02_convertir_parquet.py
uv run scripts/04_checks.py
```

## Author

Iván Dujaut — [ivandujaut.com](https://ivandujaut.com). Full bilingual writeup
will live there; this repo is the evidence.
