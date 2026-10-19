

## Before you start

**The system itself has to be agentic.** This is the part candidates most often get wrong, so we are being explicit. Using Cursor to help you write a parser is not what we are asking for. We are asking you to build a multi-step agent that does the schema inference and mapping work itself, at runtime, on a source it has not seen before. The test is simple: if we handed your submission a seventh dataset tomorrow, could it produce a mapping config without you writing anything? If the answer is no, you have built the wrong thing, however good the code is. This applies to Part 2. Part 1 can be as deterministic as you like.

**Cost:** the task is designed to cost under USD $10 in API spend. Keep your receipts — we ask you to report actual spend. If you would rather not use paid APIs, a local model is completely acceptable and we will judge the result on the same terms.

---

## Context

Firma maintains a resolved graph of Australian and New Zealand businesses — roughly 15 million companies today. The problem we are solving is that adding a new public data source currently costs an engineer several weeks: someone reads the schema, writes a connector, writes a transformer, and writes the logic that links each record to the right company.

There are thousands of useful public sources — company registers, building approvals, trade licences, workplace safety notices, court lists, procurement contracts. At an engineer-month per source, the ten-thousandth source is never worth loading. We think that maths changed. We want to find out whether adding a source can become **a review rather than a build**: a model infers the schema, proposes the mapping, and a human approves it.

This assignment is a small, real version of that problem.

Two things we care about more than most teams:

1. **A wrong link is worse than no link.** One bad merge quietly corrupts every answer built on top of it. We would always rather return nothing.
2. **Config beats code.** A solution that works for six sources because you wrote six parsers has not solved anything. A solution that works for six sources because you wrote one engine and six config files might.
3. **The configs have to be written by the agent, not by you.** One engine plus six hand-authored configs is the same problem as six parsers, moved sideways. The agent inspects the source, proposes the mapping, checks its own work, and emits the config. Your job is the system that does that, and the review step a human uses to accept or reject what it produces.


## How we will assess it

Roughly in this order:

| **Is it agentic?** | Part 2 built as a multi-step system that maps a source it has not seen, or a person doing the mapping with AI help |
| --- | --- |
| **Does it generalise?** | One engine and six configs, or six scripts wearing a trench coat |
| **Mapping quality** | Correct, and honest about what it could not map |
| **Resolution judgment** | Sensible confidence, real abstention, measured precision |
| **Profile assembly** | Field-level confidence, visible conflict handling, provenance kept |
| **Measurement** | You know your own numbers and did not round them in your favour |
| **Engineering** | It runs, it is legible, it is reproducible |
| **Judgment** | The write-up |

Things that will count against a submission: mapping configs you wrote by hand; a single prompt doing the whole inference with no validation or revision step; per-source hand-tuned parsers; a single blended confidence score covering several different kinds of uncertainty; links reported without a precision number; 100% coverage claims; ignoring the licence terms attached to a dataset.

We are not scoring English. Write however you write.

## Questions

Ask them. Sending this task and then penalising you for clarifying it would be a strange thing for us to do. If something is ambiguous, either ask or make a decision and note it in the README — both are fine.

---

## Expected repo shape

This repository should be treated as a runnable submission, not as a loose notebook dump.

The final repo should contain:

- `README.md` — how to run the project from a clean checkout in under 10 minutes.
- `WRITEUP.md` — the two-page Part 5 assessment.
- `assets/` — ontology and support files.
- `outputs/` or similar — shortlist, mapping configs, canonical observations, links, unlinked queue, and company profiles.
- Code implementing the generic engine and per-source configs.
- Any files used to hand-check precision or document assumptions.

If a part is missing or a step is broken, state that plainly in the README rather than leaving the reviewer to discover it.

---

## Required interpretation of the task

This project has five parts and they are intentionally cumulative:

1. Part 1: discover and triage data sources.
2. Part 2: infer schema and produce mapping configs for six sources.
3. Part 3: identify and link the same businesses across sources.
4. Part 4: build merged company profiles with provenance and disagreement handling.
5. Part 5: write a short judgmental summary of the system and its trade-offs.

The main thing we are evaluating is not whether you can write a parser for one source. It is whether your system can generalise: one engine with configs, not one script per source.

---

## Agent workflow required

For Part 2 in particular, the agent should behave like a multi-step system, not a single prompt. A valid workflow looks roughly like this:

1. Inspect the dataset and identify what it actually is.
2. Sample the raw data and infer schema or layout.
3. Propose a mapping against the ontology.
4. Run the mapping over unseen rows or additional sample records.
5. Check for failures: missing fields, malformed values, wrong record shapes, unhandled nesting, and schema drift.
6. Revise the mapping config and rerun validation.
7. Only then ask a human for approval.

A single prompt that directly emits a mapping without a validation loop is not enough.

The system should carry state between steps: inferred schema, candidate mappings, validation failures, revised config, and human approval decisions.

---

## Good engineering standards

- Prefer deterministic logic for the initial triage phase.
- Use the model primarily where a schema is ambiguous or needs revision.
- Record confidence per field, not one single blended score for an entire dataset.
- Leave uncertain fields unmapped instead of guessing.
- Keep provenance for every value that makes it into a profile or link.
- If a source resists, document the failure mode and what would justify custom handling.

---

## Output expectations

For Part 1, the output should be programmatic and explicit:

- at least 200 catalogue records retrieved by code
- 50 ranked candidates with confidence and reason
- a transparent estimate of false positives from a random sample of 20

For Part 2, the output should be:

- six mapping configs, one per source
- one generic extractor that consumes configs and emits canonical observations
- validation evidence showing the config survived a fresh pass over sample data

For Part 3, the output should be:

- proposed links with confidence and evidence
- unlinked queue with reasons for abstention
- measured precision from a hand-checked sample

For Part 4, the output should be:

- one company profile per linked entity
- per-field confidence and provenance
- explicit conflict handling when values disagree

For Part 5, the output should be:

- a concise write-up covering cost, agent design, hardest source, scale, change management, and next steps

---

## CLI requirement for each part

This is a reasonable and expected requirement for a submission like this.

Each part of the project should have a clear command-line entry point so a reviewer can run it independently and see the output without hand-editing code or notebooks. The goal is not necessarily to make a polished product for every stage, but to make the repository demonstrably runnable and testable stage by stage.

A good pattern is:

- `python -m firma.cli part1`
- `python -m firma.cli part2`
- `python -m firma.cli part3`
- `python -m firma.cli part4`
- `python -m firma.cli part5`

Or, if the project prefers a different structure, an equivalent command such as:

- `uv run python -m firma.part1`
- `uv run python -m firma.part2`
- etc.

What matters is that:

- each part has a single obvious command to run it,
- the command produces the artefact for that part,
- the command exits with useful logging or a summary,
- failures are visible, not silent,
- downstream parts can consume the files created by earlier commands.

Thin orchestration wrappers are fine. A part can be implemented by a small CLI that invokes the engine, writes JSON/CSV outputs, and prints a short validation summary. The rule is not "build a full interface"; the rule is "make each part runnable".

A reviewer should be able to do the following without reading the code:

1. run Part 1 and verify it fetched and ranked the catalogue data,
2. run Part 2 and verify it produced six mappings and canonical observations,
3. run Part 3 and verify it produced links and an unlinked queue,
4. run Part 4 and verify it produced profiles with provenance,
5. run Part 5 and verify it generated the write-up.

If a part is intentionally incomplete or deliberately skipped, the CLI should say so clearly, not fail mysteriously or silently.

---

## Failure modes to avoid

The following are not acceptable as a final submission:

- hand-writing six mapping configs by hand
- a single prompt doing the whole inference without a revision loop
- custom code per dataset instead of a generic engine
- ungrounded confidence scores with no traceability
- silent data loss or blank values where a field is genuinely missing
- claiming perfect precision or full coverage without measurement
- ignoring dataset licence constraints or source terms

---

## Human approval gate

A human should be asked to approve the mapping only after the system has:

- inspected the source,
- drafted a mapping,
- validated it on unseen rows,
- surfaced what it could not map confidently,
- and recorded any unresolved ambiguity.

The approval step is not a substitute for validation. It is the checkpoint that lets a reviewer confirm the agent got the nontrivial parts right.

---

## Scope discipline

This is not a general-purpose data wrangling challenge. The scope is to show that a system can ingest messy public data, infer mappings, produce canonical outputs, and reason responsibly about uncertainty and entity identity.

The strongest solution is the one that is honest about uncertainty, records provenance, and proves generalisation with config-driven execution rather than bespoke source-specific scripts.

---

## Questions

Ask them. Sending this task and then penalising you for clarifying it would be a strange thing for us to do. If something is ambiguous, either ask or make a decision and note it in the README — both are fine.