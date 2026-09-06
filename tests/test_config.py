from pathlib import Path

from gsy_profilecard.config import load_config


def test_env_txt_fallback(tmp_path: Path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    parent = tmp_path
    (parent / "env.txt").write_text("ACCESS_TOKEN=abc123\n", encoding="utf-8")
    monkeypatch.delenv("ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    cfg = load_config(root)
    assert cfg.access_token == "abc123"
    assert cfg.any_token == "abc123"


def test_env_var_takes_precedence(tmp_path: Path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    parent = tmp_path
    (parent / "env.txt").write_text("ACCESS_TOKEN=fromfile\n", encoding="utf-8")
    monkeypatch.setenv("ACCESS_TOKEN", "fromenv")
    cfg = load_config(root)
    assert cfg.access_token == "fromenv"


def test_bare_token_line(tmp_path: Path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    parent = tmp_path
    (parent / "env.txt").write_text("ghp_bareValue\n", encoding="utf-8")
    monkeypatch.delenv("ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    cfg = load_config(root)
    assert cfg.access_token == "ghp_bareValue"


def test_no_token_available(tmp_path: Path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    monkeypatch.delenv("ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    cfg = load_config(root)
    assert cfg.any_token is None
