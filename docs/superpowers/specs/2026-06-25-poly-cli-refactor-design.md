# `poly` CLI — full-parity refactor — Design Spec

**Date:** 2026-06-25
**Status:** Approved (design); ready for implementation planning
**Repo:** `polymarket_cli` (github.com/johnsonice/polymarket_cli)
**Supersedes the structure of:** `2026-06-25-poly-cli-design.md` (the original buy/sell-only tool)

---

## 1. Purpose

Refactor the current narrow `poly buy` / `poly sell` tool into an official-CLI-style
`poly <group> <verb>` command suite with a global `-o/--output json|table`, and grow it to
cover essentially all of the Rust `Polymarket/polymarket-cli`'s functionality on top of the
Python `polymarket-client` SDK — **except** `bridge` and a few trivial server-meta endpoints
the SDK doesn't expose.

## 2. Guiding constraints (do not violate)

This is the most important section. The user explicitly asked: **don't over-engineer; keep the
repo human-readable.**

- **KISS over cleverness.** No speculative abstractions, no plugin systems, no metaprogramming,
  no auto-generating commands from a method map. A reader should follow any command top-to-bottom.
- **Thin command bodies.** A command function: resolve a client → call one py-sdk method →
  `emit()` the result. Validation/business logic lives in `orders.py`; everything else is glue.
- **Many small files.** One Typer sub-app per group (~30–120 lines each), 800-line hard cap.
- **Minimal dependencies.** Add only `typer`. Drop `python-dotenv`. No `rich`/`tabulate` —
  a tiny hand-rolled table renderer is enough.
- **One obvious way to do a thing.** Errors handled in one place; output formatted in one place;
  clients built in one place. Don't repeat these per command.
- **Preserve the safety model** (preview + typed-YES + `--dry-run`) and the **type-3 deposit
  wallet default**.

## 3. Foundational decisions (settled)

| Decision | Choice |
|---|---|
| Framework | **Typer** (nested groups, global options, auto-help) |
| Wallet/key | `~/.config/polymarket/config.json` (chmod 600); resolution `--private-key` > `POLYMARKET_PRIVATE_KEY` env > config file. **Drop project `.env`.** Full `poly wallet` group. |
| Trading verbs | Official `poly clob create-order` / `clob market-order` **plus** friendly `poly buy` / `poly sell` aliases. |
| Output | Global `-o/--output` with `table` (default) or `json`. |
| Signature type | Configurable 0/1/2/3, **default 3 (deposit wallet)** — deliberately diverges from the official CLI's `proxy` default. |
| Tables | Small hand-rolled renderer, no extra dep. |
| Pagination | `--limit`/`--offset` (match official) + `--all`. |

## 4. Architecture

```
poly/
  cli.py            # root Typer app; global -o/--private-key/--signature-type; mounts groups; buy/sell aliases; main()
  context.py        # CliContext: output format + lazy public()/secure() client factories
  config.py         # config.json load/save; key resolution; Settings; build_public_client/build_secure_client
  output.py         # emit(ctx, data); table vs json; pydantic/Decimal/datetime serialization; error envelope
  pagination.py     # collect(paginator, limit, all_) -> list
  orders.py         # (existing) validation/sizing/build; reused by clob_trade + buy/sell
  market.py         # (existing) target resolution; reused by buy/sell
  groups/
    __init__.py
    markets.py events.py tags.py series.py comments.py profiles.py sports.py
    clob_read.py clob_trade.py clob_rewards.py
    data.py approve.py ctf.py wallet.py setup.py shell.py
tests/
    test_config.py test_output.py test_orders.py test_market.py
    test_clob_trade.py test_data.py test_markets.py ...  (one per group with real logic)
```

Each `groups/*.py` exposes a Typer `app`; `cli.py` does `app.add_typer(markets.app, name="markets")`.
`buy`/`sell` are top-level `@app.command()`s that build the same order plan as `clob_trade` and reuse
`orders.py` + `market.py`.

### Command body pattern (the whole tool looks like this)
```python
@app.command("list")
def list_markets(ctx: typer.Context, limit: int = 20, offset: int = 0, active: bool | None = None):
    """List markets."""
    client = public(ctx)
    page = client.list_markets(active=active, page_size=limit).first_page()
    emit(ctx, [m.model_dump(mode="json") for m in page.items])
```

### Error & output handling (one place each)
- `cli.main()` runs the Typer app with `standalone_mode=False` inside a `try/except`. On
  `ValueError | PolymarketError | SystemExit(str)`: JSON mode prints `{"error": "..."}` to stdout,
  table mode prints `Error: ...` to stderr; exit non-zero. Normal `click`/Typer exits pass through.
- `emit(ctx, data)`: `json` → `print(json.dumps(data, indent=2))`; `table` → render list-of-dicts as
  aligned columns or a single dict as key/value rows. Pydantic models are converted with
  `model_dump(mode="json")` (handles `Decimal`→str, `datetime`→ISO) before emit.

## 5. Command surface & py-sdk mapping

**In scope** (verified against the installed `polymarket-client`):

- `markets` list/get/search/tags → `list_markets`/`get_market`/`search`/`get_market_tags`
- `events` list/get/tags → `list_events`/`get_event`/`get_event_tags`
- `tags` list/get/related/related-tags → `list_tags`/`get_tag`/`get_related_tags`/`get_related_tag_resources`
- `series` list/get → `list_series`/`get_series`
- `comments` list/get/by-user → `list_comments`/`get_comment_thread`/`list_comments_by_user_address`
- `profiles get` → `get_public_profile`
- `sports` list/market-types/teams → `get_sports`/`get_sports_market_types`/`list_teams`
- `clob` reads → `get_price(s)`/`get_midpoint(s)`/`get_spread(s)`/`get_order_book(s)`/`get_last_trade_price(s)`/`get_price_history`; `market`/`markets` via `get_market`/`list_markets(condition_ids=)`; `tick-size`/`fee-rate`/`neg-risk` derived from `get_market` (`trading.minimum_tick_size`, `neg_risk`) + `get_builder_fee_rates`
- `clob` trade → `create_limit_order`/`place_limit_order`, `create_market_order`/`place_market_order`, `post_orders`, `cancel_order`/`cancel_orders`/`cancel_market_orders`/`cancel_all`, `list_open_orders`, `get_order`, `list_account_trades`, `get_balance_allowance` (update-balance via re-query)
- `clob` rewards/api → `list_user_earnings_for_day`/`get_total_earnings_for_user_for_day`/`list_user_earnings_and_markets_config`/`get_reward_percentages`/`list_current_rewards`/`list_market_rewards`/`get_order_scoring`/`get_orders_scoring`/`fetch_api_keys`/`delete_api_key`/`get_notifications`/`drop_notifications`; `account-status` via `get_closed_only_mode`; `create-api-key` is auto in `SecureClient.create`
- `data` → `list_positions`/`list_closed_positions`/`get_portfolio_values`/`get_traded_market_count`/`list_trades`/`list_activity`/`get_market_holders`/`get_open_interests`/`get_event_live_volumes`/`list_trader_leaderboard`/`list_builder_leaderboard`/`get_builder_volumes`
- `approve` check/set → `get_balance_allowance` (check) / `setup_trading_approvals` + `approve_erc20` + `approve_erc1155_for_all` (set)
- `ctf` split/merge/redeem → `split_position`/`merge_positions`/`redeem_positions`; `redeem-neg-risk` via `redeem_positions` params; `condition-id` via `to_ctf_condition_id` (collection/position-id via the SDK's internal calc helpers)
- `wallet` create/import/show/address/reset → local config.json + `eth_account` (key gen) — not an SDK feature
- `setup` → guided wizard (create/import key → write config → optional approvals)
- `shell` → interactive REPL over the same app
- top-level `buy`/`sell` → reuse `orders.py`/`market.py` (slug/url/outcome + usd convenience)

**Excluded:** `bridge` (deposit/supported-assets/status — not in py-sdk), `clob ok`/`time`/`geoblock`
(server-meta — not in py-sdk), `upgrade` (use `uv`/`pip`), `status` (trivial health).

## 6. Wallet, config & safety

- **Config file:** `~/.config/polymarket/config.json` `{ "private_key": "0x…", "signature_type": 3 }`,
  created with mode `0600`. Never written into the repo.
- **Key resolution:** `--private-key` flag > `POLYMARKET_PRIVATE_KEY` env > config file. Friendly
  error if none and the command needs a wallet.
- **Migration:** `python-dotenv` removed; `.env` no longer read. `poly setup` / `poly wallet import 0x…`
  moves the user's existing `.env` key into the config file (one time).
- **Default signature type 3** (deposit wallet); overridable via config or `--signature-type`.
- **Trading safety:** `create-order`/`market-order`/`buy`/`sell` keep the preview + typed-`YES`
  (skippable with `--yes`) + `--dry-run` (build/sign, never submit). Market BUY keeps the `max_spend`
  cap. On-chain `approve set` and `ctf` mutating ops require their own typed-`YES` (gasless via the
  relayer for deposit wallets).
- **Author guardrail (unchanged):** Claude only ever runs `--dry-run`; the user executes real
  trades/approvals/on-chain actions.

## 7. Testing

- One offline test module per group with real logic, mocking `PublicClient`/`SecureClient`
  (extend the existing `FakePub`/`FakeSecureClient`). Pure read groups get light "calls the right
  method + emits" tests; trading/ctf/approve get full safety-path tests (dry-run never posts,
  confirmation gating, side-aware validation).
- `output.py`: json vs table rendering, error envelope in both modes, Decimal/datetime serialization.
- `config.py`: resolution order, config read/write, 0600 perms, missing-key error.
- Target ≥80% on logic-bearing modules; the SDK/network boundary stays uncovered by design.

## 8. Phased implementation

- **P0 — skeleton:** Typer root + global flags; `config.py` (config.json + resolution); `output.py`
  (emit + error envelope); `pagination.py`; `wallet` + `setup` (key migration). Move `orders.py`/
  `market.py` in. Update `pyproject.toml` (add `typer`, `eth-account` if not transitive; drop
  `python-dotenv`).
- **P1 — trading + core reads:** `clob` create-order/market-order/post-orders/cancel*/orders/order/
  trades/balance; `buy`/`sell` aliases; `data positions`/`value`. (Daily driver; matches the read
  commands originally requested.)
- **P2 — public data:** markets/events/tags/series/comments/profiles/sports + `clob` reads + rest of `data`.
- **P3 — rewards/api/notifications/account-status.**
- **P4 — on-chain:** `approve` (check/set), `ctf` (split/merge/redeem/redeem-neg-risk/id-calc).
- **P5 — interactive `shell`.**

Each phase: code + tests + offline/dry-run verification, then a commit. The tool is usable and
releasable after every phase.

## 9. Open risks

- `polymarket-client` is **beta (0.1.0b9)**; method names/shapes may shift — pin the version,
  and keep command bodies thin so changes are localized.
- A few clob metadata reads (tick-size/fee-rate/neg-risk) and `ctf` id calcs need small glue rather
  than a 1:1 SDK call; verify each against the live SDK during its phase (dry-run/offline).
- Interactive `shell` is the least essential; if Typer/Click REPL integration adds complexity that
  hurts readability, it can be dropped without affecting the rest (it's P5, isolated).
