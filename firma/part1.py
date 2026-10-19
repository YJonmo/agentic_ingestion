import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import requests

CKAN_PORTALS = [
    "https://data.gov.au/data",
    "https://data.nsw.gov.au/data",
    "https://data.qld.gov.au/data",
    "https://data.vic.gov.au/data",
    "https://data.sa.gov.au/data",
]

BUSINESS_TERMS = {
    "business": 8,
    "company": 7,
    "corporation": 9,
    "enterprise": 6,
    "supplier": 7,
    "vendor": 7,
    "trading name": 8,
    "organisation": 6,
    "organization": 6,
    "proprietor": 6,
    "charity": 5,
    "not-for-profit": 5,
    "registered business": 10,
    "business name": 10,
    "company name": 10,
    "entity": 6,
    "premises": 4,
    "local business": 7,
    "small business": 7,
    "large business": 7,
}

ENTITY_HINTS = {
    "ABN": "ABN",
    "Australian Business Number": "ABN",
    "ACN": "ACN",
    "Australian Company Number": "ACN",
    "business registration": "registration",
    "company register": "company register",
    "business register": "business register",
    "charity register": "charity register",
    "supplier register": "supplier register",
    "vendor register": "vendor register",
    "trading name": "trading name",
    "registered office": "registered office",
    "organisation name": "organisation name",
    "organization name": "organization name",
}


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(_as_text(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(_as_text(item) for item in value)
    return str(value)


def _coalesce_text(record: Dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = record.get(key)
        if value is None:
            continue
        text = _as_text(value)
        if text.strip():
            return text
    return ""


def _dataset_text(record: Dict[str, Any]) -> str:
    organization = record.get("organization") or {}
    title = _coalesce_text(record, "title")
    notes = _coalesce_text(record, "notes", "description")
    organization_title = _coalesce_text(organization, "title", "name")
    tags = " ".join(_as_text(tag) for tag in record.get("tags", []) or [])
    resources = " ".join(
        _as_text(resource.get("name", ""))
        for resource in record.get("resources", []) or []
    )
    extras = " ".join(
        _as_text(extra.get("value", ""))
        for extra in record.get("extras", []) or []
    )
    return " ".join(part for part in [title, notes, organization_title, tags, resources, extras] if part)


def rank_datasets(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Rank catalogue records by likelihood of containing identifiable Australian business entities."""
    ranked: List[Dict[str, Any]] = []

    for record in records:
        text = _dataset_text(record).lower()
        score = 0
        reasons = set()

        for keyword, weight in BUSINESS_TERMS.items():
            if keyword in text:
                score += weight
                reasons.add(keyword)

        for phrase, label in ENTITY_HINTS.items():
            if phrase.lower() in text:
                score += 8
                reasons.add(label)

        if re.search(r"\babn\b|\baustralian business number\b|\bacn\b|\baustralian company number\b", text):
            score += 12
            if "abn" in text or "australian business number" in text:
                reasons.add("ABN")
            if "acn" in text or "australian company number" in text:
                reasons.add("ACN")

        if any(term in text for term in ["licensed", "licence", "licensing"]):
            score += 4
            reasons.add("licensing")

        if any(term in text for term in ["supplier", "vendor"]):
            score += 6
            reasons.add("supplier")

        if any(pattern in text for pattern in ["company register", "business register", "charity register", "registered office"]):
            score += 10
            reasons.add("register")

        confidence = max(0.0, min(0.99, score / 100))
        ranked.append(
            {
                "id": record.get("id"),
                "title": record.get("title") or "Untitled dataset",
                "organization": (record.get("organization") or {}).get("title") or "Unknown organization",
                "confidence": round(confidence, 3),
                "score": min(score, 100),
                "reasons": sorted(reasons),
            }
        )

    return sorted(ranked, key=lambda item: (item["score"], item["title"].lower()), reverse=True)


def shortlist_business_entity_datasets(records: Sequence[Dict[str, Any]], limit: int = 50) -> List[Dict[str, Any]]:
    """Return the top-ranked likely business-entity datasets."""
    ranked = rank_datasets(records)
    return [item for item in ranked if item["score"] > 0][:limit]


def fetch_ckan_action(portal_url: str, action: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    base_url = portal_url.rstrip("/")
    response = requests.get(
        f"{base_url}/api/3/action/{action}",
        params=params or {},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("success") is not True:
        raise ValueError(f"CKAN action failed: {payload}")
    return payload.get("result", {})


def collect_catalogue_records(
    portals: Sequence[str] | None = None,
    min_records: int = 200,
    rows_per_request: int = 200,
    search_terms: Sequence[str] | None = None,
) -> List[Dict[str, Any]]:
    """Retrieve a pool of at least min_records dataset records from CKAN portals."""
    portal_list = list(portals or CKAN_PORTALS)
    search_list = list(search_terms or [
        "business",
        "company",
        "supplier",
        "vendor",
        "charity",
        "trading name",
        "business name",
        "entity",
        "licence",
        "organization",
    ])

    collected: List[Dict[str, Any]] = []
    seen_ids = set()

    for portal_url in portal_list:
        for term in search_list:
            result = fetch_ckan_action(
                portal_url,
                "package_search",
                {"q": term, "rows": rows_per_request, "start": 0},
            )
            for record in result.get("results", []):
                record_id = record.get("id")
                if record_id and record_id not in seen_ids:
                    seen_ids.add(record_id)
                    collected.append(record)
            if len(collected) >= min_records:
                return collected[:min_records]

    return collected


def write_csv(rows: Iterable[Dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id",
        "title",
        "organization",
        "resource_formats",
        "confidence",
        "reason",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            resource_formats = ", ".join(
                resource.get("format", "unknown")
                for resource in row.get("resources", []) or []
            ) or "unknown"
            writer.writerow(
                {
                    "id": row.get("id"),
                    "title": row.get("title"),
                    "organization": (row.get("organization") or {}).get("title") or "Unknown",
                    "resource_formats": resource_formats,
                    "confidence": row.get("confidence"),
                    "reason": "; ".join(row.get("reasons", [])),
                }
            )


def write_jsonl(rows: Iterable[Dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def run_part1(
    portals: Sequence[str] | None = None,
    min_records: int = 200,
    limit: int = 50,
    search_terms: Sequence[str] | None = None,
    output_dir: Path | str = "outputs/part1",
) -> List[Dict[str, Any]]:
    records = collect_catalogue_records(
        portals=portals,
        min_records=min_records,
        search_terms=search_terms,
    )
    if len(records) < min_records:
        raise ValueError(f"Only collected {len(records)} records; expected at least {min_records}.")

    shortlist = shortlist_business_entity_datasets(records, limit=limit)
    output_path = Path(output_dir)
    jsonl_path = output_path / "shortlist.jsonl"
    csv_path = output_path / "shortlist.csv"

    rows_for_output = []
    for row in shortlist:
        record = next(item for item in records if item.get("id") == row["id"]) if any(item.get("id") == row["id"] for item in records) else {}
        row_payload = {
            "id": row["id"],
            "title": row["title"],
            "organization": {"title": row["organization"]},
            "resources": record.get("resources", []),
            "confidence": row["confidence"],
            "reasons": row["reasons"],
        }
        rows_for_output.append(row_payload)

    write_jsonl(rows_for_output, jsonl_path)
    write_csv(rows_for_output, csv_path)

    summary_path = output_path / "summary.json"
    summary = {
        "portal_count": len(portals or CKAN_PORTALS),
        "records_collected": len(records),
        "shortlist_size": len(shortlist),
        "false_positive_sample_size": 20,
        "false_positive_estimate": None,
        "notes": "Hand-check a random sample of 20 shortlisted records to fill in the false-positive estimate.",
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return shortlist
