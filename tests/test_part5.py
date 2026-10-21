from firma.part5 import run_part5


def test_run_part5_writes_summary_file(tmp_path):
    output = tmp_path / "WRITEUP.md"
    report = run_part5(output_path=output)

    assert output.exists()
    assert "Part 5" in report
    assert "Cost" in report
    assert "Agent design" in report
    assert "Hardest source" in report
