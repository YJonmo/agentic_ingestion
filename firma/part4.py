"""Build merged company profiles from linked observations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _read_observations(observations_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not observations_dir.exists():
        return rows
    for path in sorted(observations_dir.glob("*.jsonl")):
        rows.extend(_read_jsonl(path))
    return rows


def _field_confidence(field_conf: dict[str, Any] | None, default: float = 0.5) -> float:
    if not isinstance(field_conf, dict):
        return default
    value = field_conf.get("field_confidence")
    if isinstance(value, (int, float)):
        return float(value)
    return default


def assemble_profiles(observations: list[dict[str, Any]], links: list[dict[str, Any]]) -> list[dict[str, Any]]:
    linked_record_keys: set[tuple[str, str]] = set()
    link_lookup: dict[tuple[str, str], str] = {}
    for link in links:
        left = link.get("source_a_record") or {}
        right = link.get("source_b_record") or {}
        if not left or not right:
            continue
        left_key = (str(left.get("source_id", "")), str(left.get("source_record_id", "")))
        right_key = (str(right.get("source_id", "")), str(right.get("source_record_id", "")))
        linked_record_keys.add(left_key)
        linked_record_keys.add(right_key)
        link_lookup[left_key] = link.get("canonical_entity_key") or "unlinked"
        link_lookup[right_key] = link.get("canonical_entity_key") or "unlinked"

    entity_groups: dict[str, list[dict[str, Any]]] = {}
    for observation in observations:
        source_id = str((observation.get("observation") or {}).get("source_id") or "")
        record_id = str((observation.get("observation") or {}).get("source_record_id") or "")
        if not source_id or not record_id:
            continue
        key = (source_id, record_id)
        entity_key = link_lookup.get(key)
        if entity_key is None:
            entity_key = f"unlinked:{source_id}:{record_id}"
        entity_groups.setdefault(entity_key, []).append(observation)

    profiles: list[dict[str, Any]] = []
    for entity_key, members in sorted(entity_groups.items()):
        merged: dict[str, Any] = {}
        provenance: dict[str, list[dict[str, Any]]] = {}
        conflicts: list[dict[str, Any]] = []
        for observation in members:
            entity = observation.get("entity") or {}
            source_id = str((observation.get("observation") or {}).get("source_id") or "")
            record_id = str((observation.get("observation") or {}).get("source_record_id") or "")
            for field, value in entity.items():
                if value in (None, ""):
                    continue
                key = field
                if key not in merged:
                    merged[key] = {
                        "value": value,
                        "confidence": _field_confidence((observation.get("confidence") or {}).get("field_confidence", {}).get(field)),
                        "source": {"source_id": source_id, "source_record_id": record_id},
                        "evidence": [f"source={source_id}:{record_id}"],
                    }
                    provenance[key] = [{
                        "source_id": source_id,
                        "source_record_id": record_id,
                        "value": value,
                        "confidence": _field_confidence((observation.get("confidence") or {}).get("field_confidence", {}).get(field)),
                    }]
                elif str(merged[key]["value"]).lower() != str(value).lower():
                    conflicts.append({
                        "field": key,
                        "values": [str(merged[key]["value"]), str(value)],
                        "winner": merged[key]["value"],
                        "reason": "Keep the higher-confidence value from the more trusted observation and record the disagreement.",
                    })
                    if _field_confidence((observation.get("confidence") or {}).get("field_confidence", {}).get(field)) > merged[key]["confidence"]:
                        merged[key] = {
                            "value": value,
                            "confidence": _field_confidence((observation.get("confidence") or {}).get("field_confidence", {}).get(field)),
                            "source": {"source_id": source_id, "source_record_id": record_id},
                            "evidence": [f"source={source_id}:{record_id}"],
                        }
                    provenance.setdefault(key, []).append({
                        "source_id": source_id,
                        "source_record_id": record_id,
                        "value": value,
                        "confidence": _field_confidence((observation.get("confidence") or {}).get("field_confidence", {}).get(field)),
                    })
                else:
                    provenance.setdefault(key, []).append({
                        "source_id": source_id,
                        "source_record_id": record_id,
                        "value": value,
                        "confidence": _field_confidence((observation.get("confidence") or {}).get("field_confidence", {}).get(field)),
                    })

        profile = {
            "entity_key": entity_key,
            "profile": {field: {"value": meta["value"], "confidence": meta["confidence"], "source": meta["source"], "evidence": meta["evidence"]} for field, meta in merged.items()},
            "provenance": provenance,
            "conflicts": conflicts,
        }
        profiles.append(profile)

    return profiles


def _load_links(path: Path | str | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    link_path = Path(path)
    if not link_path.exists():
        return []
    return _read_jsonl(link_path)


def run_part4(observations_dir: Path | str = "outputs/part2/observations",
             output_dir: Path | str = "outputs/part4",
             links_path: Path | str | None = "outputs/part3/links.jsonl",
             explicit_links: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    observations_dir = Path(observations_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    links = explicit_links if explicit_links is not None else _load_links(links_path)
    observations = _read_observations(observations_dir)
    profiles = assemble_profiles(observations, links)

    with (output_dir / "profiles.jsonl").open("w", encoding="utf-8") as handle:
        for profile in profiles:
            handle.write(json.dumps(profile, ensure_ascii=False) + "\n")

    summary = {
        "profile_count": len(profiles),
        "entity_keys": [profile["entity_key"] for profile in profiles],
        "notes": "Each profile keeps field-level confidence, provenance, and conflict history; values are only replaced when the newer item has higher confidence.",
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary
