# tests/test_cli_global.py
from typer.testing import CliRunner
from poly.cli import app
from poly import context

runner = CliRunner()


def test_global_output_flag_parses():
    # `buy --help` should render with the global -o flag present
    result = runner.invoke(app, ["-o", "json", "buy", "--help"])
    assert result.exit_code == 0


def test_unknown_command_is_clean_error():
    result = runner.invoke(app, ["definitely-not-a-command"])
    assert result.exit_code != 0


def test_signature_type_flag_is_gone():
    """--signature-type must no longer be a recognized option."""
    result = runner.invoke(app, ["--signature-type", "3", "wallet", "show"])
    assert result.exit_code != 0


def test_error_envelope_for_value_error(monkeypatch):
    """A ValueError raised inside a command returns exit code 1 and prints an error."""
    from poly.groups import data as data_mod

    def _raise_value_error(ctx, address):
        raise ValueError("synthetic error for test")

    monkeypatch.setattr(data_mod, "_resolve_user", _raise_value_error)
    result = runner.invoke(app, ["data", "value"])
    # main() catches ValueError and returns 1
    assert result.exit_code == 1
