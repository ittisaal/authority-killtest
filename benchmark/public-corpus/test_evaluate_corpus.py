import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).parent
spec = importlib.util.spec_from_file_location("evaluate_corpus", ROOT / "evaluate_corpus.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_frozen_labels():
    data = json.loads((ROOT / "corpus.json").read_text())
    got = {c["id"]: mod.classify(c)[0] for c in data["cases"]}
    expected = {c["id"]: c["expected_label"] for c in data["cases"]}
    assert got == expected


def test_baselines_on_known_binary_subset():
    data = json.loads((ROOT / "corpus.json").read_text())
    assert mod.confusion(data["cases"], mod.baseline_editable) == {
        "TP": 1, "FP": 2, "TN": 3, "FN": 0
    }
    assert mod.confusion(data["cases"], mod.baseline_editable_consumed) == {
        "TP": 1, "FP": 1, "TN": 4, "FN": 0
    }
