# tests/test_clob_trade.py
from decimal import Decimal
from types import SimpleNamespace
from typer.testing import CliRunner
from poly.cli import app
from poly import context

runner = CliRunner()


class FakePub:
    def list_markets(self, clob_token_ids=None):
        return SimpleNamespace(first_page=lambda: SimpleNamespace(items=[]))
    def get_price(self, token_id=None, side=None): return Decimal("0.5")


class FakeSecure:
    wallet = "0xWALLET"
    def __init__(self): self.posted = []
    def create_limit_order(self, **k):
        return SimpleNamespace(maker=self.wallet, signer=self.wallet, token_id=k["token_id"],
                               side=k["side"], maker_amount="1", taker_amount="2", order_type="GTC")
    def post_order(self, s): self.posted.append(s); return SimpleNamespace(ok=True, order_id="o1", status="MATCHED")
    def list_open_orders(self, **k):
        return SimpleNamespace(first_page=lambda: SimpleNamespace(items=[{"id": "o1", "price": "0.5"}], has_next=False))


def test_create_order_dry_run_does_not_post(monkeypatch):
    fake = FakeSecure()
    monkeypatch.setattr(context, "public", lambda ctx: FakePub())
    monkeypatch.setattr(context, "secure", lambda ctx: fake)
    result = runner.invoke(app, ["clob", "create-order", "--token", "111", "--side", "buy",
                                 "--size", "5", "--price", "0.5", "--dry-run"])
    assert result.exit_code == 0
    assert fake.posted == []


def test_orders_read_json(monkeypatch):
    monkeypatch.setattr(context, "secure", lambda ctx: FakeSecure())
    result = runner.invoke(app, ["-o", "json", "clob", "orders"])
    assert result.exit_code == 0 and "o1" in result.output
