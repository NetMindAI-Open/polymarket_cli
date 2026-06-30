import json
import pytest
from poly import config


def test_resolve_prefers_flag_then_env_then_config():
    assert config.resolve_private_key(flag="0xf", env="0xe", config="0xc") == "0xf"
    assert config.resolve_private_key(flag=None, env="0xe", config="0xc") == "0xe"
    assert config.resolve_private_key(flag=None, env=None, config="0xc") == "0xc"
    assert config.resolve_private_key() is None


def test_save_config_is_chmod_600(tmp_path):
    p = tmp_path / "config.json"
    config.save_config({"private_key": "0xabc"}, path=p)
    assert json.loads(p.read_text())["private_key"] == "0xabc"
    assert (p.stat().st_mode & 0o777) == 0o600


def test_load_settings_requires_key(tmp_path, monkeypatch):
    monkeypatch.delenv("POLYMARKET_PRIVATE_KEY", raising=False)
    with pytest.raises(SystemExit):
        config.load_settings(path=tmp_path / "missing.json")


def test_load_settings_normalizes_0x_prefix(tmp_path):
    p = tmp_path / "config.json"
    config.save_config({"private_key": "abc"}, path=p)
    s = config.load_settings(path=p)
    assert s.private_key == "0xabc"


def test_load_settings_ignores_stale_signature_type(tmp_path, monkeypatch):
    """A config with a non-integer 'signature_type' value must not raise."""
    monkeypatch.delenv("POLYMARKET_PRIVATE_KEY", raising=False)
    p = tmp_path / "config.json"
    p.write_text(json.dumps({"private_key": "0xabc", "signature_type": "proxy"}))
    s = config.load_settings(path=p)
    assert s.private_key == "0xabc"


def test_resolve_environment_defaults_to_production(monkeypatch):
    for env in config._URL_ENV.values():
        monkeypatch.delenv(env, raising=False)
    from polymarket.environments import PRODUCTION
    assert config.resolve_environment() is PRODUCTION


def test_resolve_environment_overrides_only_set_urls(monkeypatch):
    for env in config._URL_ENV.values():
        monkeypatch.delenv(env, raising=False)
    monkeypatch.setenv("POLYMARKET_CLOB_URL", "http://proxy:7001")
    monkeypatch.setenv("POLYMARKET_GAMMA_URL", "http://proxy:7002")
    from polymarket.environments import PRODUCTION
    env = config.resolve_environment()
    # overridden
    assert env.clob_url == "http://proxy:7001"
    assert env.gamma_url == "http://proxy:7002"
    # untouched URLs stay production
    assert env.data_url == PRODUCTION.data_url
    # chain id + contract addresses MUST stay production (order signatures depend on them)
    assert env.chain_id == PRODUCTION.chain_id
    assert env.collateral_token == PRODUCTION.collateral_token
    assert env.standard_exchange == PRODUCTION.standard_exchange
