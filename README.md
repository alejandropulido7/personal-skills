# personal-skills — agent-agnostic port

A collection of personal **agents**, **skills**, **trading strategies**, and
**reusable scripts** that work under **any AI coding agent**: Hermes Agent,
Gemini CLI, Claude Code, Codex, raw shell, etc.

## Path resolution

Every reference to skill or strategy files uses one of two environment
variables, resolved at runtime:

| Variable | Default (Hermes) | Fallbacks |
| --- | --- | --- |
| `SKILLS_DIR` | `${HOME}/.hermes/skills` | `${HOME}/.gemini/config/skills`, `${HOME}/.claude/skills` |
| `STRATEGIES_DIR` | `${HOME}/.hermes/trading-strategies` | `${HOME}/.gemini/config/trading-strategies`, `${HOME}/.claude/trading-strategies` |

**Resolution rule** (POSIX shell, used inside `bash` snippets in the
skill files):

```bash
SKILLS_DIR="${SKILLS_DIR:-${HOME}/.hermes/skills}"
STRATEGIES_DIR="${STRATEGIES_DIR:-${HOME}/.hermes/trading-strategies}"
```

To override per agent, export the variable before invoking the skill.

## Layout

```
personal-skills/
├── agents/                  10 agent profiles (architect, code-reviewer, tdd-guide, ...)
├── skills/                  28 reusable skills (dev + trading)
├── trading-strategies/      5 strategy YAMLs (CRT, ICT, NAS100, ORB, SMC)
├── projects/                1 example project template
├── scripts/port_to_hermes.sh  Migration helper (no longer needed, kept for reference)
└── README.md
```

## Quick install per agent

### Hermes Agent

```bash
# Skills go to ~/.hermes/skills/ — the default. Just copy or symlink.
ln -s "$(pwd)/skills"/* ~/.hermes/skills/
mkdir -p ~/.hermes/trading-strategies
ln -s "$(pwd)/trading-strategies"/* ~/.hermes/trading-strategies/
# Agents can be registered in ~/.hermes/agents/ if your version supports it.
```

### Gemini CLI

```bash
SKILLS_DIR=~/.gemini/config/skills STRATEGIES_DIR=~/.gemini/config/trading-strategies
ln -s "$(pwd)/skills"/* "$SKILLS_DIR"/
ln -s "$(pwd)/trading-strategies"/* "$STRATEGIES_DIR"/
```

### Claude Code / Claude Desktop

```bash
SKILLS_DIR=~/.claude/skills
mkdir -p "$SKILLS_DIR"
ln -s "$(pwd)/skills"/* "$SKILLS_DIR"/
# Strategies: drop them wherever your config points. If unsure:
mkdir -p ~/.claude/trading-strategies
ln -s "$(pwd)/trading-strategies"/* ~/.claude/trading-strategies/
```

## What's in the trading skills

The `skills/scan-*` family (ICT, ORB, SMC, CRT, NAS100) is a complete
multi-timeframe validation pipeline that:

1. Reads the active symbol from your TradingView watchlist.
2. Extracts OHLCV at 1H/15m/5m via `tradingview-ohlcv`.
3. Applies the strategy's entry rules to detect setups.
4. Draws the levels (FVG, OB, SR, SL/TP, Entry) on the chart via
   `tradingview-drawings`.
5. Generates a technical report (Entry / SL / TP / R:R).

The `skills/trade-review/` family automates the post-mortem (MFE / MAE / R:R
realized, whether the trade hit TP/SL, and what the chart looks like now).

The `skills/create-trading-strategy/` skill is a structured interview that
turns a trading idea into a validated YAML strategy + a corresponding
`scan-*` skill.

## Disclaimer

Trading financial instruments involves significant risk. These skills are
provided for personal/educational/research use only. You are solely
responsible for your trading decisions and any consequences thereof.
