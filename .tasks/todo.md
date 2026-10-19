# Firma Project Task Breakdown

This file defines the work to be completed in sequence. Each task is meant to be executed by an agent or developer, with a clear checkpoint and validation step at the end of each task.

## Task 1: Repository bootstrap and project setup

Goal: Create the project skeleton and the minimal tooling needed to run the pipeline locally.

Requirements:
- Initialize the repository structure for a Python-based data pipeline.
- Add a README with setup instructions.
- Create a Python virtual environment using uv.
- Add dependency management with a minimal requirements or uv configuration.
- Add a `.gitignore` covering local env files, outputs, caches, and generated data.
- Confirm the environment runs and can import the project package.

Acceptance criteria:
- A clean repo structure exists.
- A developer can run the project from a fresh clone in under 10 minutes.
- `python -c "import pkg"` or equivalent works for the main package.

Validation:
- Run `git status` and confirm only intended project files are tracked.
- Run a minimal smoke command from the project root.

---

## Task 2: Dataset discovery and triage pipeline

Goal: Build a deterministic discovery engine that retrieves at least 200 CKAN catalogue records and filters them to a shortlist of likely business-entity datasets.

Requirements:
- Use the CKAN Action API from data.gov.au and optionally state portals.
- Retrieve a pool of at least 200 records programmatically.
- Build a scoring function for likely Australian business-entity datasets.
- Rank results and produce a shortlist of the top 50 datasets.
- Export the shortlist in CSV or JSONL format.
- Include dataset ID, title, publishing organisation, resource format(s), confidence, and one-line reason.

Acceptance criteria:
- At least 200 source records are gathered by code.
- A ranked output of 50 candidate datasets is produced.
- Each shortlisted dataset includes the required metadata.
- The system can explain why a record was included.

Validation:
- Check the record count is at least 200.
- Inspect the shortlist head and ensure fields are present and sane.
- Hand-check a small random subset to estimate false positives.

---

## Task 3: False positive audit and precision reporting

Goal: Measure how honest the shortlist is and report precision.

Requirements:
- Randomly sample 20 datasets from the 50-item shortlist.
- Manually assess whether each dataset actually contains identifiable Australian business entities.
- Report false positive rate and precision.
- Document how the count was computed and whether the result is honest or approximate.

Acceptance criteria:
- A measured precision report exists for the shortlist.
- A sample of 20 is explicitly reviewed.
- The report distinguishes between actual found business entities and false positives.

Validation:
- Ensure the number of true positives and false positives is stated explicitly.
- Record the method used for the random sample.

---

## Task 4: Ontology review and source selection

Goal: Prepare the six sources needed for Part 2 by selecting datasets that are realistic and diverse.

Requirements:
- Choose six datasets from the shortlist that are downloadable and structurally different.
- Prefer variation across publisher, format, and data shape.
- At least one dataset should not be a clean CSV.
- Confirm a raw sample can be read and inspected.

Acceptance criteria:
- Six data sources are selected and recorded.
- The resources are different enough to exercise the generic mapping engine.
- At least one messy or non-tabular source is included.

Validation:
- Inspect the first few records from each source.
- Verify the source types and schemas are diverse.

---

## Task 5: Schema inspection and source profiling

Goal: Build the first phase of the agentic mapping tool: inspect each source and determine its true structure before doing mapping.

Requirements:
- Create a source inspection step that identifies file type, schema, columns, delimiters, and record layout.
- Sample each resource and summarize its structure.
- Determine likely field names and whether they are nested, repeated, or ambiguous.
- Record observations in a machine-readable report for each of the six sources.

Acceptance criteria:
- Every chosen source has a schema/profile summary.
- The inspection output captures important irregularities.
- The pipeline can operate on unseen sources by running this step first.

Validation:
- Run the inspector on each source and confirm captured fields are accurate.
- Confirm non-standard sources are identified before mapping.

---

## Task 6: Mapping proposal engine

Goal: Implement the multi-step mapping agent that proposes canonical mappings from raw source fields to the ontology.

Requirements:
- Read the ontology file from `assets/firma_ontology.yaml`.
- Build a proposal step that maps source fields to canonical fields.
- Include transformations where needed (string normalization, date parsing, field renames, cleaning, category mapping, etc.).
- Keep fields confident when they are strong and leave uncertain fields unmapped rather than guessing.
- Record per-field source, target, transformation, and confidence.

Acceptance criteria:
- A machine-readable mapping config is produced for each of the six sources.
- Uncertain mappings are clearly left unmapped.
- Each mapping records confidence and transformations.

Validation:
- Run proposals over sample records and check that they produce plausible canonical observations.
- Confirm no field is silently guessed without confidence.

---

## Task 7: Validate mapping proposals against unseen data

Goal: Cause the agent to check its own mapping work before human approval.

Requirements:
- Use a validation pass over held-out or unseen rows from each source.
- Evaluate whether the mapping assumptions hold.
- Revise the mapping if field extraction fails, values are malformed, or record shape differs.
- Record the revision cycle and why mapping changes were made.

Acceptance criteria:
- Each mapping has a self-check step.
- Validation failures trigger revision rather than silent success.
- The mapping config reflects the final validated version.

Validation:
- Run the validator on a subset of records not used in proposal.
- Confirm mismatches are logged and corrected.

---

## Task 8: Generic extractor implementation

Goal: Build one generic extractor that consumes a mapping config and emits canonical observations.

Requirements:
- The extractor must read a mapping file and transform raw records accordingly.
- It should support the canonical ontology structure used in the project.
- It should be generic enough to be reused by all six sources.
- It should produce canonical observations in a consistent format.

Acceptance criteria:
- One engine handles the six mapping configs.
- It can process at least 1,000 sample records from each source.
- Output is machine-readable and consistent.

Validation:
- Run the extractor on each selected source and inspect output shape.
- Verify canonical observation schema matches the ontology.

---

## Task 9: Canonical observations output

Goal: Generate canonical observations for each source from the extractor.

Requirements:
- For each of the six sources, run the generic extractor over a sample of 1,000 records.
- Save the canonical outputs to a consistent folder and format.
- Include evidence of output shape and field coverage.

Acceptance criteria:
- Six output files exist for canonical observations.
- Each output corresponds to a source and is machine-readable.
- Standard fields from the ontology are present where mapped.

Validation:
- Inspect a few rows from each output.
- Check data types and required fields are consistent.

---

## Task 10: Entity identification and proposed links

Goal: Build the matching logic that identifies same businesses across multiple sources.

Requirements:
- Design a business matching model across the six processed sources.
- Generate proposed links with the fields: `source_a_record`, `source_b_record`, `canonical_entity_key`, `confidence`, and `evidence`.
- Define a confidence threshold and provide the rationale.
- Keep an explicit unlinked queue for suspicious or ambiguous business records.

Acceptance criteria:
- Proposed links exist for records that are confidently the same business.
- Ambiguous records are excluded and documented.
- The link model explains why relationships are represented as chosen.

Validation:
- Sample the link list and manually check a subset.
- Ensure the threshold policy is applied consistently.

---

## Task 11: Precision measurement for links

Goal: Measure link quality honestly.

Requirements:
- Hand-check 50 proposed links.
- Report how many are correct.
- State the threshold used for inclusion.
- For each measured precision result, explain whether the threshold is strict or loose.

Acceptance criteria:
- 50 sampled links are assessed.
- Precision is reported numerically and clearly.
- The threshold and methodology are documented.

Validation:
- Ensure a random or representative subset is used.
- Keep a log of the judgments for traceability.

---

## Task 12: Company profiles

Goal: Build one merged profile record per linked business across the six sources.

Requirements:
- Take 50 linked entities and merge the information from all sources.
- Include field-level confidence, not just one score for the whole profile.
- Record provenance for each value.
- Show disagreements and why a value won.
- Leave absent fields absent rather than blank.

Acceptance criteria:
- 50 profiles exist.
- Each profile shows field-level confidence and provenance.
- Conflicting values are documented and explained.

Validation:
- Inspect profiles to ensure provenance and disagreement handling are visible.
- Confirm empty values are not silently invented.

---

## Task 13: Write-up and cost explanation

Goal: Produce Part 5 in a concise, professional write-up.

Requirements:
- Write a two-page maximum `WRITEUP.md` covering:
  1. Cost and actual spend/tokens
  2. Agent design and failure modes
  3. Hard source and why it resisted
  4. Scale breakdown between 6 and 500 sources
  5. Change management for millions of historical links
  6. Next steps with three weeks instead of six hours
- Include a brief explanation of how entity relationships were modelled in Part 3.

Acceptance criteria:
- The write-up is concise, readable, and grounded in actual project results.
- It states explicitly where data is estimated or unknown.

Validation:
- Read the write-up as if a reviewer is judging it.
- Ensure it matches the actual project architecture and results.

---

## Task 14: Final repo assembly and verification

Goal: Package the final project in a clean, runnable form.

Requirements:
- Ensure `README.md` explains how to run the system from a clean checkout in under 10 minutes.
- Add any required outputs and configuration files.
- Make sure all generated materials are present.
- Document any broken or incomplete areas honestly.

Acceptance criteria:
- The repository is complete and runnable.
- The README tells the user the exact setup and execution path.
- Any limitations are clearly called out rather than hidden.

Validation:
- Run a reproducible smoke test from a clean checkout path.
- Verify all required deliverables are present in the repo.

---

## Recommended execution order

1. Task 1
2. Task 2
3. Task 3
4. Task 4
5. Task 5
6. Task 6
7. Task 7
8. Task 8
9. Task 9
10. Task 10
11. Task 11
12. Task 12
13. Task 13
14. Task 14

## Notes for future agents

- Each task should be self-contained and produce artifacts that later tasks can consume.
- Later tasks must not rely on hidden memory; all relevant state should be stored in files.
- If a task fails, the agent should leave a clear note explaining why, what was tested, and what next action is required.
- Prefer deterministic, explainable work early, and keep the agentic layer focused on schema inference and revision rather than writing custom parser logic for each dataset.
