import argparse
from pathlib import Path

from firma.part1 import run_part1
from firma.part2 import run_part2
from firma.part3 import run_part3
from firma.part4 import run_part4
from firma.part5 import run_part5
from firma.export import export_ingestion


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Firma pipeline commands")
    subparsers = parser.add_subparsers(dest="command", required=True)

    part1_parser = subparsers.add_parser("part1", help="Fetch and rank likely business-entity datasets")
    part1_parser.add_argument("--min-records", type=int, default=200)
    part1_parser.add_argument("--limit", type=int, default=50)
    part1_parser.add_argument("--search-terms", nargs="*", default=None, help="Keywords used to search CKAN metadata")
    part1_parser.add_argument("--output-dir", type=Path, default=Path("outputs/part1"))

    part2_parser = subparsers.add_parser("part2", help="Inspect sources, propose and validate mappings, and extract observations")
    part2_parser.add_argument("--shortlist", type=Path, default=Path("outputs/part1/shortlist.jsonl"))
    part2_parser.add_argument("--ontology", type=Path, default=Path("assets/firma_ontology.yaml"))
    part2_parser.add_argument("--output-dir", type=Path, default=Path("outputs/part2"))
    part2_parser.add_argument("--limit", type=int, default=6)
    part2_parser.add_argument("--sample-limit", type=int, default=1200)

    part3_parser = subparsers.add_parser("part3", help="Link observations across sources and emit an unlinked queue")
    part3_parser.add_argument("--observations-dir", type=Path, default=Path("outputs/part2/observations"))
    part3_parser.add_argument("--output-dir", type=Path, default=Path("outputs/part3"))

    part4_parser = subparsers.add_parser("part4", help="Merge linked observations into company profiles with provenance")
    part4_parser.add_argument("--observations-dir", type=Path, default=Path("outputs/part2/observations"))
    part4_parser.add_argument("--links", type=Path, default=Path("outputs/part3/links.jsonl"))
    part4_parser.add_argument("--output-dir", type=Path, default=Path("outputs/part4"))

    part5_parser = subparsers.add_parser("part5", help="Write the final assessment summary for the Firma project")
    part5_parser.add_argument("--output", type=Path, default=Path("WRITEUP.md"))
    part5_parser.add_argument("--source-manifest", type=Path, default=Path("outputs/part2/source_manifest.json"))
    part5_parser.add_argument("--part3-summary", type=Path, default=Path("outputs/part3/summary.json"))
    part5_parser.add_argument("--part4-summary", type=Path, default=Path("outputs/part4/summary.json"))

    export_parser = subparsers.add_parser("export", help="Bundle graph inputs for downstream ingestion")
    export_parser.add_argument("--observations-dir", type=Path, default=Path("outputs/part2/observations"))
    export_parser.add_argument("--source-manifest", type=Path, default=Path("outputs/part2/source_manifest.json"))
    export_parser.add_argument("--links", type=Path, default=Path("outputs/part3/links.jsonl"))
    export_parser.add_argument("--profiles", type=Path, default=Path("outputs/part4/profiles.jsonl"))
    export_parser.add_argument("--output-dir", type=Path, default=Path("outputs/ingestion"))

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "part1":
        shortlist = run_part1(
            min_records=args.min_records,
            limit=args.limit,
            search_terms=args.search_terms,
            output_dir=args.output_dir,
        )
        print(f"Collected and ranked {len(shortlist)} candidate datasets.")
        print(f"Output written to {args.output_dir}")
        return

    if args.command == "part2":
        report = run_part2(
            shortlist_path=args.shortlist,
            ontology_path=args.ontology,
            output_dir=args.output_dir,
            limit=args.limit,
            sample_limit=args.sample_limit,
        )
        valid_count = sum(result["validation_passed"] for result in report["results"])
        print(f"Processed {len(report['results'])} sources with LangGraph and OpenAI.")
        print(f"Held-out validation passed for {valid_count}/{len(report['results'])} sources.")
        print(f"Output written to {args.output_dir}; mapping approval remains pending.")
        return

    if args.command == "part3":
        summary = run_part3(
            observations_dir=args.observations_dir,
            output_dir=args.output_dir,
        )
        print(f"Loaded {summary['observations_loaded']} observations and proposed {summary['link_count']} links.")
        print(f"Unlinked queue contains {summary['unlinked_count']} records.")
        print(f"Output written to {args.output_dir}")
        return

    if args.command == "part4":
        summary = run_part4(
            observations_dir=args.observations_dir,
            links_path=args.links,
            output_dir=args.output_dir,
        )
        print(f"Built {summary['profile_count']} company profiles.")
        print(f"Output written to {args.output_dir}")
        return

    if args.command == "part5":
        report = run_part5(
            output_path=args.output,
            source_manifest_path=args.source_manifest,
            part3_summary_path=args.part3_summary,
            part4_summary_path=args.part4_summary,
        )
        print(f"Part 5 write-up generated at {args.output}")
        print("Summary includes cost, agent design, hardest source, scale, and next steps.")
        return

    if args.command == "export":
        output_dir = export_ingestion(
            observations_dir=args.observations_dir,
            source_manifest_path=args.source_manifest,
            links_path=args.links,
            profiles_path=args.profiles,
            output_dir=args.output_dir,
        )
        print(f"Graph-ingestion artifacts exported to {output_dir}")
        return

    raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
