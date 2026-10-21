import json

from firma.part3 import build_links, build_unlinked_queue, run_part3


def _observation(source_id: str, record_id: str, legal_name: str, abn: str | None = None, acn: str | None = None):
    return {
        "entity": {"legal_name": legal_name, "abn": abn or "", "acn": acn or ""},
        "observation": {"source_id": source_id, "source_record_id": record_id},
        "confidence": {"field_confidence": {}},
    }


def test_build_links_groups_same_business_identifiers():
    observations = [
        _observation("src_a", "1", "Example Pty Ltd", abn="12345678901"),
        _observation("src_b", "7", "Example Pty Limited", abn="12345678901"),
        _observation("src_c", "42", "Unknown Co", abn="99999999999"),
    ]

    links = build_links(observations)
    assert len(links) == 1
    assert links[0]["canonical_entity_key"] == "abn:12345678901"
    assert links[0]["confidence"] >= 0.95
    assert links[0]["source_a_record"]["source_id"] == "src_a"
    assert links[0]["source_b_record"]["source_id"] == "src_b"

    unlinked = build_unlinked_queue(observations, links)
    assert any(item["source_id"] == "src_c" for item in unlinked)


def test_run_part3_writes_link_and_unlinked_outputs(tmp_path):
    obs_dir = tmp_path / "observations"
    obs_dir.mkdir()
    file_a = obs_dir / "a.jsonl"
    file_b = obs_dir / "b.jsonl"
    file_a.write_text(
        json.dumps(_observation("src_a", "1", "Example Pty Ltd", abn="12345678901")) + "\n"
        + json.dumps(_observation("src_a", "2", "Unique Pty Ltd", abn="11111111111")) + "\n",
        encoding="utf-8",
    )
    file_b.write_text(
        json.dumps(_observation("src_b", "7", "Example Pty Limited", abn="12345678901")) + "\n"
        + json.dumps(_observation("src_b", "8", "Different Co", abn="22222222222")) + "\n",
        encoding="utf-8",
    )

    out_dir = tmp_path / "out"
    report = run_part3(observations_dir=obs_dir, output_dir=out_dir)

    assert report["link_count"] == 1
    assert report["unlinked_count"] == 2
    assert (out_dir / "links.jsonl").exists()
    assert (out_dir / "unlinked_queue.jsonl").exists()
