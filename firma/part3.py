"""Link matching observations across sources and emit an unlinked queue."""

from __future__ import annotations

import itertools
import json
import re
from pathlib import Path
from typing import Any


def _normalise_name(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(value).lower()).split())


def _record_key(observation: dict[str, Any]) -> tuple[str, str]:
    obs_meta = observation.get("observation", {}) if isinstance(observation, dict) else {}
    source_id = str(obs_meta.get("source_id") or "unknown")
    record_id = str(obs_meta.get("source_record_id") or "unknown")
    return source_id, record_id


def _observation_identity(observation: dict[str, Any]) -> dict[str, str]:
    entity = observation.get("entity", {}) if isinstance(observation, dict) else {}
    result: dict[str, str] = {}
    for field in ("abn", "acn", "nzbn"):
        value = entity.get(field)
        if value not in (None, ""):
            result[field] = re.sub(r"\D", "", str(value))
    legal_name = entity.get("legal_name")
    if legal_name not in (None, ""):
        result["legal_name_normalized"] = _normalise_name(legal_name)
    address = observation.get("address", {}) if isinstance(observation, dict) else {}
    if isinstance(address, dict):
        state = address.get("state")
        if state not in (None, ""):
            result["state"] = _normalise_name(state)
    return result


def _evidence_for_pair(left: dict[str, Any], right: dict[str, Any], key: str) -> list[str]:
    evidence: list[str] = []
    shared = None
    if key.startswith("abn:"):
        shared = "ABN"
    elif key.startswith("acn:"):
        shared = "ACN"
    elif key.startswith("nzbn:"):
        shared = "NZBN"
    elif key.startswith("name:"):
        shared = "normalized legal name"
    if shared:
        evidence.append(f"Shared {shared} match: {key}")
    left_name = _normalise_name((left.get("entity") or {}).get("legal_name"))
    right_name = _normalise_name((right.get("entity") or {}).get("legal_name"))
    if left_name and right_name and left_name == right_name:
        evidence.append("Normalized legal names match exactly.")
    return evidence if evidence else ["Observed a shared canonical business identifier."]


def _link_confidence(left: dict[str, Any], right: dict[str, Any], key: str) -> float:
    if key.startswith(("abn:", "acn:", "nzbn:")):
        return 0.99
    left_name = _normalise_name((left.get("entity") or {}).get("legal_name"))
    right_name = _normalise_name((right.get("entity") or {}).get("legal_name"))
    if left_name and right_name and left_name == right_name:
        return 0.88
    return 0.75


def build_links(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build pairwise links for observations that share strong business keys."""
    buckets: dict[str, list[dict[str, Any]]] = {}
    for observation in observations:
        identity = _observation_identity(observation)
        for field, value in identity.items():
            if field in {"abn", "acn", "nzbn"}:
                bucket_key = f"{field}:{value}"
                buckets.setdefault(bucket_key, []).append(observation)
            elif field == "legal_name_normalized" and value:
                buckets.setdefault(f"name:{value}", []).append(observation)

    links: list[dict[str, Any]] = []
    seen_pairs: set[tuple[tuple[str, str], tuple[str, str]]] = set()
    for key, bucket in buckets.items():
        if len(bucket) < 2:
            continue
        for left, right in itertools.combinations(bucket, 2):
            left_record = _record_key(left)
            right_record = _record_key(right)
            pair = tuple(sorted((left_record, right_record)))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            links.append({
                "source_a_record": {"source_id": left_record[0], "source_record_id": left_record[1]},
                "source_b_record": {"source_id": right_record[0], "source_record_id": right_record[1]},
                "canonical_entity_key": key,
                "confidence": round(_link_confidence(left, right, key), 4),
                "evidence": _evidence_for_pair(left, right, key),
                "link_type": "identifier_match" if key.startswith(("abn:", "acn:", "nzbn:")) else "name_match",
            })
    return sorted(links, key=lambda item: (item["canonical_entity_key"], item["confidence"]))


def build_unlinked_queue(observations: list[dict[str, Any]], links: list[dict[str, Any]]) -> list[dict[str, Any]]:
    linked_records: set[tuple[str, str]] = set()
    for link in links:
        left = link["source_a_record"]
        right = link["source_b_record"]
        linked_records.add((str(left["source_id"]), str(left["source_record_id"])))
        linked_records.add((str(right["source_id"]), str(right["source_record_id"])))

    queue: list[dict[str, Any]] = []
    for observation in observations:
        record = _record_key(observation)
        if record in linked_records:
            continue
        identity = _observation_identity(observation)
        if identity.get("abn") or identity.get("acn") or identity.get("nzbn"):
            reason = "Identifier present but no other observation shared the same canonical business key."
        elif identity.get("legal_name_normalized"):
            reason = "Name-only record had no sufficiently strong match above the confidence threshold."
        else:
            reason = "No usable business identifier was available for a confident link."
        queue.append({
            "source_id": record[0],
            "source_record_id": record[1],
            "reason": reason,
            "entity": observation.get("entity", {}),
        })
    return queue


def _load_observations(observations_dir: Path) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    if not observations_dir.exists():
        return observations
    for path in sorted(observations_dir.glob("*.jsonl")):
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                if isinstance(payload, dict):
                    observations.append(payload)
    return observations


def run_part3(observations_dir: Path | str = "outputs/part2/observations",
             output_dir: Path | str = "outputs/part3") -> dict[str, Any]:
    observations_dir = Path(observations_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    observations = _load_observations(observations_dir)
    links = build_links(observations)
    unlinked = build_unlinked_queue(observations, links)

    with (output_dir / "links.jsonl").open("w", encoding="utf-8") as handle:
        for link in links:
            handle.write(json.dumps(link, ensure_ascii=False) + "\n")

    with (output_dir / "unlinked_queue.jsonl").open("w", encoding="utf-8") as handle:
        for item in unlinked:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")

    summary = {
        "link_count": len(links),
        "unlinked_count": len(unlinked),
        "observations_loaded": len(observations),
        "precision_estimate": None,
        "notes": "Only deterministic identifier and normalized-name matches are used for proposal; ambiguous candidates are left in the unlinked queue.",
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary
