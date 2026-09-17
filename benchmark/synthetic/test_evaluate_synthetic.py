import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("evaluate_synthetic", HERE / "evaluate_synthetic.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def load_cases():
    return json.loads((HERE / "cases.json").read_text())


def test_all_expected_observations_reproduce():
    result = module.evaluate(load_cases())
    assert result["summary"]["observation_matches"] == result["summary"]["observation_total"] == 9


def test_complete_evidence_matches_semantic_truth():
    result = module.evaluate(load_cases())
    assert result["summary"]["complete_evidence_cases"] == 7
    assert result["summary"]["complete_evidence_truth_matches"] == 7


def test_incomplete_views_abstain():
    result = module.evaluate(load_cases())
    assert result["summary"]["incomplete_evidence_cases"] == 2
    assert result["summary"]["incomplete_cases_returning_N"] == 2


def test_expected_mix():
    result = module.evaluate(load_cases())
    assert result["summary"]["predicted_counts"] == {"U": 3, "S": 4, "N": 2}


def test_N_is_not_semantic_truth_class():
    assert all(case["semantic_truth"] in {"U", "S"} for case in load_cases()["cases"])
