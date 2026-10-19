import argparse
from pathlib import Path

from firma.part1 import run_part1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Firma pipeline commands")
    subparsers = parser.add_subparsers(dest="command", required=True)

    part1_parser = subparsers.add_parser("part1", help="Fetch and rank likely business-entity datasets")
    part1_parser.add_argument("--min-records", type=int, default=200)
    part1_parser.add_argument("--limit", type=int, default=50)
    part1_parser.add_argument("--search-terms", nargs="*", default=None, help="Keywords used to search CKAN metadata")
    part1_parser.add_argument("--output-dir", type=Path, default=Path("outputs/part1"))

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

    raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
