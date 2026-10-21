import json

from firma.part4 import assemble_profiles, run_part4


def _observation(source_id: str, record_id: str, legal_name: str, abn: str | None = None):
    return {
        "entity": {"legal_name": legal_name, "abn": abn or ""},
        "observation": {"source_id": source_id, "source_record_id": record_id},
        "confidence": {"field_confidence": {"legal_name": {"field_confidence": 0.9}, "abn": {"field_confidence": 0.95}}},
    }


def test_assemble_profiles_merges_linked_observations_and_records_conflicts():
    observations = [
        _observation("src_a", "1", "Example Pty Ltd", "12345678901"),
        _observation("src_b", "7", "Example Pty Limited", "12345678901"),
        _observation("src_c", "42", "Other Pty Ltd", "99999999999"),
    ]
    links = [
        {
            "source_a_record": {"source_id": "src_a", "source_record_id": "1"},
            "source_b_record": {"source_id": "src_b", "source_record_id": "7"},
            "canonical_entity_key": "abn:12345678901",
            "confidence": 0.99,
            "evidence": ["Shared ABN match: abn:12345678901"],
        }
    ]

    profiles = assemble_profiles(observations, links)
    assert len(profiles) == 2
    linked = [profile for profile in profiles if profile["entity_key"] == "abn:12345678901"][0]
    assert linked["profile"]["legal_name"]["value"] in {"Example Pty Ltd", "Example Pty Limited"}
    assert linked["profile"]["abn"]["value"] == "12345678901"
    assert linked["conflicts"][0]["field"] == "legal_name"


def test_run_part4_writes_profiles_and_summary(tmp_path):
    obs_dir = tmp_path / "observations"
    obs_dir.mkdir()
    (obs_dir / "a.jsonl").write_text(
        json.dumps(_observation("src_a", "1", "Example Pty Ltd", "12345678901")) + "\n"
        + json.dumps(_observation("src_a", "2", "Other Pty Ltd", "99999999999")) + "\n",
        encoding="utf-8",
    )
    (obs_dir / "b.jsonl").write_text(
        json.dumps(_observation("src_b", "7", "Example Pty Limited", "12345678901")) + "\n",
        encoding="utf-8",
    )
    links = [
        {
            "source_a_record": {"source_id": "src_a", "source_record_id": "1"},
            "source_b_record": {"source_id": "src_b", "source_record_id": "7"},
            "canonical_entity_key": "abn:12345678901",
            "confidence": 0.99,
            "evidence": ["Shared ABN match."],
        }
    ]
    out_dir = tmp_path / "out"
    summary = run_part4(links_path=None, observations_dir=obs_dir, output_dir=out_dir, explicit_links=links)

    assert summary["profile_count"] == 2
    assert (out_dir / "profiles.jsonl").exists()
    assert (out_dir / "summary.json").exists()
