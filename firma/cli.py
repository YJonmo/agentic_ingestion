import argparse
from pathlib import Path

from firma.part1 import run_part1
from firma.part2 import run_part2


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

    raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
