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

## Task 2: schema inference and mapping

Put `OPENAI_API_KEY` in the local `.env` file. Optionally set `OPENAI_MODEL`
(defaults to `gpt-4o-mini`). `.env` is ignored by Git.

Run the LangGraph workflow after Part 1:

```bash
python -m firma.cli part2
```

The graph profiles each selected source, asks the OpenAI model for a structured
ontology mapping, validates that proposal against held-out rows, and asks the model
for one revision when checks fail. Deterministic validation remains the safety gate;
fields that still fail are left unmapped. Mapping approval remains `pending` for human
review. Generated profiles, mappings, validation reports, and observations are written
under `outputs/part2/`.

## Task 3: cross-source linking

After Part 2 has produced observation files, run the linking stage:

```bash
python -m firma.cli part3
```

This reads the observation JSONL files under `outputs/part2/observations`, proposes
links for records that share the same canonical identifier or normalized legal name,
and writes the results to `outputs/part3/`.

## Task 4: company profiles

After Part 3 has produced links, build merged company profiles:

```bash
python -m firma.cli part4
```

This reads the linked records and assembles one profile per canonical entity, with
field-level confidence, provenance, and recorded disagreements.

## Project structure

- `firma/` — project package
- `outputs/part1/` — generated shortlist and metadata
- `tests/` — basic quality checks
