"""Regression test for the Phase 10 AI evaluation runner - ensures the
dataset stays loadable and the runner produces a valid report."""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EVAL_SCRIPT = REPO_ROOT / "evaluation" / "run_eval.py"
DATASET = REPO_ROOT / "evaluation" / "dataset.json"


def test_dataset_is_valid_json_with_required_fields():
    cases = json.loads(DATASET.read_text())
    assert len(cases) >= 8
    required_case_types = {"true_positive", "false_positive", "ambiguous", "prompt_injection", "missing_data"}
    seen_types = {c["case_type"] for c in cases}
    assert required_case_types.issubset(seen_types)
    for case in cases:
        assert "case_id" in case
        assert "alert" in case
        assert "expected_classification_family" in case


def test_eval_runner_executes_and_produces_report(tmp_path):
    result = subprocess.run(
        [sys.executable, str(EVAL_SCRIPT)],
        cwd=str(REPO_ROOT / "backend"),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr

    report_json = REPO_ROOT / "evaluation" / "eval_report.json"
    assert report_json.exists()
    data = json.loads(report_json.read_text())
    assert "metrics" in data
    assert data["metrics"]["structured_output_validity_rate"] == 1.0
    assert data["metrics"]["total_cases"] >= 8
