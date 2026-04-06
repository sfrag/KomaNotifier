from pathlib import Path

from saturn_koma_watcher.storage import load_seen_ids, save_seen_ids


def test_save_and_load_state(tmp_path: Path) -> None:
    state_file = tmp_path / "state.json"
    source_ids = {"abc", "xyz"}

    save_seen_ids(state_file, source_ids)
    loaded = load_seen_ids(state_file)

    assert loaded == source_ids


def test_load_missing_state_returns_empty(tmp_path: Path) -> None:
    state_file = tmp_path / "state.json"
    loaded = load_seen_ids(state_file)
    assert loaded == set()
