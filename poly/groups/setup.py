# poly/groups/setup.py
"""First-time setup: store a key in config.json."""

import typer
from eth_account import Account

from ..config import CONFIG_PATH, load_config, save_config
from ..output import emit


def setup_cmd(ctx: typer.Context, private_key: str = typer.Option(None, "--private-key")) -> None:
    """Configure your signer key (use --private-key, or paste when prompted)."""
    key = private_key or typer.prompt("Signer private key (0x...)", hide_input=True)
    key = key if key.startswith("0x") else "0x" + key
    # Build a new dict — never mutate the existing config in place.
    # Stale keys like "signature_type" are preserved as-is (ignored by the SDK).
    save_config({**load_config(path=CONFIG_PATH), "private_key": key}, path=CONFIG_PATH)
    fmt = getattr(ctx.obj, "output", "table")
    emit(fmt, {"address": Account.from_key(key).address, "config": str(CONFIG_PATH)})
