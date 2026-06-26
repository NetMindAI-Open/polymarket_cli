# poly/groups/wallet.py
"""Local wallet/key management backed by config.json."""

import typer
from eth_account import Account

from ..config import CONFIG_PATH, load_config, save_config, load_settings
from ..output import emit
from ..context import CliContext

app = typer.Typer(no_args_is_help=True, help="Manage the signer key (config.json).")


def _fmt(ctx: typer.Context) -> str:
    return ctx.obj.output if isinstance(ctx.obj, CliContext) else "table"


def _store_key(key: str) -> str:
    key = key if key.startswith("0x") else "0x" + key
    cfg = load_config(path=CONFIG_PATH)
    cfg["private_key"] = key
    save_config(cfg, path=CONFIG_PATH)
    return Account.from_key(key).address


@app.command()
def create(ctx: typer.Context, force: bool = typer.Option(False, "--force")) -> None:
    """Generate a new random wallet and save it."""
    if load_config(path=CONFIG_PATH).get("private_key") and not force:
        raise SystemExit("A key already exists. Use --force to overwrite.")
    acct = Account.create()
    addr = _store_key(acct.key.hex())
    emit(_fmt(ctx), {"address": addr, "config": str(CONFIG_PATH)})


@app.command("import")
def import_key(ctx: typer.Context, private_key: str = typer.Argument(...)) -> None:
    """Import an existing private key."""
    addr = _store_key(private_key)
    emit(_fmt(ctx), {"address": addr, "config": str(CONFIG_PATH)})


@app.command()
def show(ctx: typer.Context) -> None:
    """Show wallet address + config path (never prints the key)."""
    cfg = load_config(path=CONFIG_PATH)
    key = cfg.get("private_key")
    addr = Account.from_key(key).address if key else None
    emit(_fmt(ctx), {"address": addr, "signature_type": cfg.get("signature_type", 3), "config": str(CONFIG_PATH)})


@app.command()
def address(ctx: typer.Context) -> None:
    """Print the wallet address."""
    pk = ctx.obj.private_key if isinstance(ctx.obj, CliContext) else None
    settings = load_settings(private_key=pk)
    emit(_fmt(ctx), {"address": Account.from_key(settings.private_key).address})


@app.command()
def reset(ctx: typer.Context, force: bool = typer.Option(False, "--force")) -> None:
    """Delete the saved config."""
    if not force:
        raise SystemExit("This deletes your saved key. Re-run with --force to confirm.")
    CONFIG_PATH.unlink(missing_ok=True)
    emit(_fmt(ctx), {"deleted": str(CONFIG_PATH)})
