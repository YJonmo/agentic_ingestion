# Part 5: System assessment

## Cost

This prototype was intentionally designed to stay cheap and reviewable rather than to brute-force every dataset. The project did not retain a precise token ledger for each API call, so I am not claiming a exact dollar spend. The honest position is that the system used a small number of source passes, capped the model to one revision per failing mapping, and operated on six sources in the main run. That kept the cost low enough to fit the assignment budget while still exercising the agentic loop. The real cost saving is architectural: a single engine and set of mappings is far cheaper to maintain than hand-written source-specific parsers.

## Agent design

The architecture is deliberately staged: Part 1 ranks candidate datasets, Part 2 profiles and maps each source to the canonical ontology with a LangGraph loop, Part 3 proposes links across observations using identifier matches and normalized names, and Part 4 assembles merged profiles with provenance and disagreement tracking. The model is used where the signal is ambiguous, but deterministic checks remain the safety gate. This is the right separation for a knowledge graph: the model proposes, the code validates, and the final graph keeps the evidence trail. The biggest design decision was to prefer abstention over false certainty. That means some records are intentionally left unlinked or unmapped, which is a feature rather than a bug.

## Hardest source

The hardest source was the ASIC company dataset because it contains a large number of historical and variant spellings, duplicate legal names across corporate histories, and a mix of valid identifiers and placeholder values. The same business can appear in multiple name variants, while some fields remain noisy or sparsely populated. This is exactly the kind of source where a naive parser would over-merge; the validation and abstention logic was needed to keep the graph honest. The dataset still worked well because the canonical business keys (ABN, ACN) and the validation layer prevented the obvious false matches from entering the link set.

## Scale

In the present repository, the system processed 6 successful sources and 2 failed fetches. The Part 2 run generated 7200 sampled rows across those sources, producing 2646 proposed links and leaving 3998 records in the unlinked queue. Part 4 then assembled 5401 merged profiles from the linked observations. That is a realistic middle ground between a toy demo and a large production graph: the pattern is already functional on a small set of sources, and the same approach generalizes by reusing the same config-driven engine rather than custom source code.

## Change management

The main operational issue in a graph like this is not data volume but schema drift and source quality. A field that was valid last month may be renamed, dropped, or reformatted next month. The fix is to keep provenance, validation histories, and mapping configs for each source instead of baking transformations into one-off scripts. This allows a dataset change to be reviewed as a config revision rather than a code rewrite. The graph remains explainable because each value can be traced back to a source field, source record, and extraction version.

## Next steps

The next improvement would be a measured link-precision study on a sample of the proposed pairs, followed by a source-reliability model and a visible graph view. A small graph database or a lightweight browser-based visualization would make the knowledge graph easier to inspect and query. The most important extension is not more custom code; it is better confidence calibration, provenance retention, and a clearer human approval step before a proposed link becomes authoritative.

This project demonstrates the right overall pattern: deterministic validation, agentic mapping, honest abstention, and a graph that keeps its evidence instead of flattening everything into a single guessed value.
