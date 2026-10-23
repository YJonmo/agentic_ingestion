import json

from firma.export import export_ingestion


def test_export_ingestion_bundles_requested_artifacts(tmp_path):
    outputs = tmp_path / "outputs"
    observations = outputs / "part2" / "observations"
    observations.mkdir(parents=True)
    (observations / "source-a.jsonl").write_text('{"entity": {"legal_name": "Example"}}\n', encoding="utf-8")

    source_manifest = outputs / "part2" / "source_manifest.json"
    source_manifest.write_text('{"results": []}', encoding="utf-8")
    links = outputs / "part3" / "links.jsonl"
    links.parent.mkdir(parents=True)
    links.write_text('{"canonical_entity_key": "abn:12345678901"}\n', encoding="utf-8")
    profiles = outputs / "part4" / "profiles.jsonl"
    profiles.parent.mkdir(parents=True)
    profiles.write_text('{"entity_key": "abn:12345678901"}\n', encoding="utf-8")

    exported = export_ingestion(
        observations_dir=observations,
        source_manifest_path=source_manifest,
        links_path=links,
        profiles_path=profiles,
        output_dir=outputs / "ingestion",
    )

    assert exported == outputs / "ingestion"
    assert (exported / "observations" / "source-a.jsonl").read_text(encoding="utf-8") == (observations / "source-a.jsonl").read_text(encoding="utf-8")
    assert json.loads((exported / "source_manifest.json").read_text(encoding="utf-8")) == {"results": []}
    assert (exported / "links.jsonl").read_text(encoding="utf-8") == links.read_text(encoding="utf-8")
    assert (exported / "profiles.jsonl").read_text(encoding="utf-8") == profiles.read_text(encoding="utf-8")
    assert observations.exists()
