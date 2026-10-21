import yaml

from firma.part2 import MappingProposal, ProposedField, build_agent


def test_langgraph_profiles_proposes_validates_and_extracts(monkeypatch):
    records = [
        {"Company Name": "  Example   Pty Ltd ", "ABN": "53004085616", "Other": "x"},
        {"Company Name": "Second Example Pty Ltd", "ABN": "53004085616", "Other": "y"},
        {"Company Name": "Third Example Pty Ltd", "ABN": "53004085616", "Other": "z"},
    ]
    monkeypatch.setattr("firma.part2.load_sample", lambda source, limit: records[:limit])
    proposal = MappingProposal(
        fields=[
            ProposedField(source_field="Company Name", target_field="legal_name", confidence=0.96,
                          rationale="Company Name identifies the registered entity.", transformation="normalize_whitespace"),
            ProposedField(source_field="ABN", target_field="abn", confidence=0.99,
                          rationale="ABN is the Australian Business Number.", transformation="digits_only"),
        ],
        notes=[],
    )
    monkeypatch.setattr("firma.part2._invoke_mapping_model", lambda state, revise=False: (proposal, "mock-gpt"))
    ontology = yaml.safe_load(open("assets/firma_ontology.yaml", encoding="utf-8"))
    source = {
        "source_id": "test-source",
        "title": "Test source",
        "format": "csv",
        "licence": "CC-BY",
        "resource": {"id": "resource-1"},
    }

    result = build_agent().invoke({"source": source, "ontology": ontology, "sample_limit": 3})

    assert result["profile"]["sample_record_count"] == 3
    assert result["validation"]["passed"] is True
    assert {field["target_field"] for field in result["mapping"]["fields"]} == {"legal_name", "abn"}
    assert len(result["observations"]) == 3
    first = result["observations"][0]
    assert first["entity"]["legal_name"] == "Example Pty Ltd"
    assert first["observation"]["source_record_id"] == "test-source:0"
    assert first["confidence"]["field_confidence"]["legal_name"]["source_field"] == "Company Name"
    assert result["approval"] == "pending"


def test_langgraph_removes_mapping_that_fails_holdout(monkeypatch):
    records = [
        {"Company Name": "First Company", "ABN": "123"},
        {"Company Name": "Second Company", "ABN": "456"},
        {"Company Name": "Third Company", "ABN": "not-an-abn"},
    ]
    monkeypatch.setattr("firma.part2.load_sample", lambda source, limit: records[:limit])
    initial = MappingProposal(
        fields=[
            ProposedField(source_field="Company Name", target_field="legal_name", confidence=0.95,
                          rationale="Company Name is a registered name.", transformation="normalize_whitespace"),
            ProposedField(source_field="ABN", target_field="abn", confidence=0.99,
                          rationale="ABN field name.", transformation="digits_only"),
        ],
        notes=[],
    )
    revised = MappingProposal(
        fields=[initial.fields[0]],
        notes=["ABN samples failed checksum/length validation; abstaining."],
    )
    calls = []

    def fake_model(state, revise=False):
        calls.append(revise)
        return (revised if revise else initial, "mock-gpt")

    monkeypatch.setattr("firma.part2._invoke_mapping_model", fake_model)
    ontology = yaml.safe_load(open("assets/firma_ontology.yaml", encoding="utf-8"))
    source = {"source_id": "test-source", "title": "Test", "format": "csv", "resource": {}}

    result = build_agent().invoke({"source": source, "ontology": ontology, "sample_limit": 3})

    assert result["validation"]["passed"] is True
    assert "ABN" in result["mapping"]["unmapped_source_fields"]
    assert "abn" not in {field["target_field"] for field in result["mapping"]["fields"]}
    assert result["revisions"][0]["removed_fields"] == ["ABN"]
    assert result["validation"]["checks"][0]["target_field"] == "legal_name"
    assert calls == [False, True]


def test_extract_skips_invalid_identifier_values(monkeypatch):
    source = {"source_id": "bad-abn-source", "title": "Bad ABN source", "format": "csv", "licence": "CC-BY"}
    state = {
        "source": source,
        "records": [{"ABN": "0", "Company Name": "Example Pty Ltd"}],
        "mapping": {
            "fields": [
                {"source_field": "ABN", "target_field": "abn", "section": "entity", "confidence": 0.9, "transformation": "digits_only"},
                {"source_field": "Company Name", "target_field": "legal_name", "section": "entity", "confidence": 0.9, "transformation": "normalize_whitespace"},
            ]
        },
    }

    from firma.part2 import _extract

    result = _extract({"source": source, "records": state["records"], "mapping": state["mapping"]})

    observation = result["observations"][0]
    assert "abn" not in observation["entity"]
    assert observation["entity"]["legal_name"] == "Example Pty Ltd"
    assert observation["observation"]["source_record_id"] == "bad-abn-source:0"