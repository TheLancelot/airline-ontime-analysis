from pathlib import Path

from app.config import BASE_DIR, resolve_app_path


def test_relative_runtime_paths_are_anchored_to_src():
    assert resolve_app_path("./data/users.json", Path("unused")) == (
        BASE_DIR / "data" / "users.json"
    ).resolve()


def test_absolute_runtime_paths_are_preserved(tmp_path):
    assert resolve_app_path(str(tmp_path / "users.json"), Path("unused")) == (
        tmp_path / "users.json"
    ).resolve()
