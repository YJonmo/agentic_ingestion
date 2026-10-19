# Firma

This repository contains the early stages of the Firma dataset triage pipeline.

## Setup

```bash
source .venv/bin/activate
uv pip install -e .
```

## Task 1: dataset discovery and ranking

Run the discovery pipeline:

```bash
python -m firma.cli part1 --min-records 200 --limit 50
```

This will:
- query the public CKAN portals,
- collect at least 200 catalog entries,
- score them for business-entity likelihood,
- write the ranked shortlist to `outputs/part1/shortlist.csv` and JSONL files.

## Project structure

- `firma/` — project package
- `outputs/part1/` — generated shortlist and metadata
- `tests/` — basic quality checks
