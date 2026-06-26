from types import SimpleNamespace
from typer.testing import CliRunner
from poly.cli import app
from poly import context
from poly.groups import data as data_mod
from poly import config as config_mod

runner = CliRunner()


class FakePub:
    def list_positions(self, user=None, page_size=20):
        return SimpleNamespace(first_page=lambda: SimpleNamespace(items=[{"outcome": "Yes", "size": "5"}], has_next=False))

    def get_portfolio_values(self, user=None):
        return {"total": "100.50", "user": user}


def test_positions_json(monkeypatch):
    monkeypatch.setattr(context, "public", lambda ctx: FakePub())
    result = runner.invoke(app, ["-o", "json", "data", "positions", "0xWALLET"])
    assert result.exit_code == 0 and "Yes" in result.output


def test_value_calls_get_portfolio_values(monkeypatch):
    monkeypatch.setattr(context, "public", lambda ctx: FakePub())
    result = runner.invoke(app, ["-o", "json", "data", "value", "0xSOMEWALLET"])
    assert result.exit_code == 0
    assert "100.50" in result.output


def test_resolve_user_defaults_to_configured_wallet(monkeypatch, tmp_path):
    """_resolve_user falls back to the wallet derived from the configured key."""
    # Use a well-known test key (ETH private key, no real funds).
    test_key = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
    from eth_account import Account
    expected_address = Account.from_key(test_key).address

    p = tmp_path / "config.json"
    import json
    p.write_text(json.dumps({"private_key": test_key}))
    monkeypatch.setattr(config_mod, "CONFIG_PATH", p)

    ctx = SimpleNamespace(obj=SimpleNamespace(private_key=None))
    resolved = data_mod._resolve_user(ctx, address=None)
    assert resolved == expected_address
