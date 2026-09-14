"""실험 데이터가 배포 재현용 학습/평가에 조용히 섞이지 않는지 검사한다."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_eye_open_gate as gate


@pytest.mark.parametrize("include", [False, True])
def test_training_data_requires_explicit_smile_opt_in(monkeypatch, include):
    calls = []
    def load(folder, key, split):
        calls.append(folder)
        return [f"{folder}/{key}/{split}"]
    monkeypatch.setattr(gate, "load_split", load)
    groups = gate.load_training_splits(include)
    for split, (opened, closed) in zip(("train", "holdout"), (groups[:2], groups[2:])):
        assert f"dataset_openeye/open/{split}" in opened
        assert f"dataset_closedeye/excluded_open_eye/{split}" in opened
        assert f"dataset_closedeye/closed/{split}" in closed
        assert (f"dataset_smileeye/open/{split}" in opened) is include
        assert (f"dataset_smileeye/closed/{split}" in closed) is include
    assert ("dataset_smileeye" in calls) is include


def test_default_does_not_load_smile_data(monkeypatch):
    def load(folder, key, split):
        assert folder != "dataset_smileeye"
        return []
    monkeypatch.setattr(gate, "load_split", load)
    assert gate.load_training_splits() == ([], [], [], [])
