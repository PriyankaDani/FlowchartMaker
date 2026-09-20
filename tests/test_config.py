"""resource_path resolves identically in dev and frozen (PyInstaller) mode (ticket 009)."""
import sys
from pathlib import Path

from flowchartmaker import config
from flowchartmaker.config import resource_path

REPO = Path(config.__file__).resolve().parents[2]


def test_dev_bundled_asset_resolves_inside_package_tree():
    p = resource_path("flowchartmaker/web/templates")

    assert p.is_dir() and (p / "index.html").exists()


def test_dev_env_resolves_to_repo_root():
    assert resource_path(".env", writable=True) == REPO / ".env"


def test_frozen_bundled_asset_uses_meipass(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path / "bundle"), raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "app" / "flowchartmaker.exe"))

    assert resource_path("flowchartmaker/web/static") == tmp_path / "bundle" / "flowchartmaker/web/static"


def test_frozen_env_uses_exe_directory_not_bundle(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path / "bundle"), raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "app" / "flowchartmaker.exe"))

    assert resource_path(".env", writable=True) == tmp_path / "app" / ".env"
