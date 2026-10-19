from firma.cli import build_parser
from firma.part1 import rank_datasets, shortlist_business_entity_datasets


def test_cli_accepts_search_terms():
    parser = build_parser()
    args = parser.parse_args(["part1", "--min-records", "200", "--limit", "50", "--search-terms", "ABN", "trading name"])

    assert args.search_terms == ["ABN", "trading name"]


def test_rank_datasets_prioritizes_business_signals():
    records = [
        {
            "id": "a1",
            "title": "Business Register Extract",
            "notes": "Contains Australian company names, ABN, ACN, and business locations.",
            "organization": {"title": "ASIC"},
            "tags": ["business", "company", "supplier"],
            "resources": [{"name": "ABN register"}],
        },
        {
            "id": "b2",
            "title": "General open data guidance",
            "notes": "General notes for data re-use.",
            "organization": {"title": "State government"},
            "tags": ["open-data"],
            "resources": [{"name": "FAQ"}],
        },
    ]

    ranked = rank_datasets(records)
    assert ranked[0]["id"] == "a1"
    assert ranked[0]["confidence"] >= ranked[1]["confidence"]
    assert "ABN" in ranked[0]["reasons"]


def test_shortlist_returns_requested_limit():
    records = [
        {
            "id": f"d-{idx}",
            "title": f"Dataset {idx}",
            "notes": "Contains business names, supplier records, and ABN references.",
            "organization": {"title": "Department of Commerce"},
            "tags": ["business", "supplier"],
            "resources": [{"name": "Supplier list"}],
        }
        for idx in range(10)
    ]

    shortlist = shortlist_business_entity_datasets(records, limit=5)
    assert len(shortlist) == 5
    assert all(item["confidence"] >= 0 for item in shortlist)
