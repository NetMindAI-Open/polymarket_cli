# tests/test_cli_global.py
from typer.testing import CliRunner
from poly.cli import app

runner = CliRunner()


def test_global_output_flag_parses():
    # `buy --help` should render with the global -o flag present
    result = runner.invoke(app, ["-o", "json", "buy", "--help"])
    assert result.exit_code == 0


def test_unknown_command_is_clean_error():
    result = runner.invoke(app, ["definitely-not-a-command"])
    assert result.exit_code != 0
