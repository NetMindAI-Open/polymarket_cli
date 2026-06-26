# tests/test_wallet.py
import json
from typer.testing import CliRunner
from poly.cli import app
from poly import config
import poly.groups.wallet as wallet_mod

runner = CliRunner()


def test_import_writes_key(tmp_path, monkeypatch):
    p = tmp_path / "config.json"
    monkeypatch.setattr(config, "CONFIG_PATH", p)
    monkeypatch.setattr(wallet_mod, "CONFIG_PATH", p)
    result = runner.invoke(app, ["wallet", "import", "0x" + "a" * 64])
    assert result.exit_code == 0
    assert json.loads(p.read_text())["private_key"] == "0x" + "a" * 64


def test_address_requires_key(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "none.json")
    monkeypatch.delenv("POLYMARKET_PRIVATE_KEY", raising=False)
    result = runner.invoke(app, ["wallet", "address"])
    assert result.exit_code != 0
