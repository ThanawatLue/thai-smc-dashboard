---
name: thai-smc-trading-system
description: Thai-market Smart Money Concept setup framework for finding entries, stops, and take-profit levels with RR 1:3 or better.
---

# Thai SMC Trading System

Use this skill when building, reviewing, or operating Smart Money Concept setups for Thai equities.

## Market Scope

- Trade universe: Thailand only.
- Symbols must use Thai tickers, normalized to `.BK`.
- Do not mix US or crypto behavior into this framework.

## Top-Down Workflow

1. HTF context: use Month, Week, Day to find major support, resistance, liquidity, and market bias.
2. H4 zones: identify nearest demand zone, supply zone, and order block.
3. H1 behavior: classify the current regime as trend, H4 zone reaction, pullback, or sideway.
4. Setup selection: choose only the playbook that matches the regime.
5. LTF trigger: use M15/M5 for retest and price-action confirmation only.

## Entry Rules

- Wait for BOS, CHoCH, or MSS to define structure.
- Identify OB, DZ in uptrend, or SZ in downtrend.
- Wait for liquidity to be created first.
- No liquidity sweep means no entry.
- After sweep, wait for rejection or displacement.
- Enter only on LTF retest and valid price action:
  - Buy: M5 forms buy PA with a second higher low at support.
  - Sell: M5 forms sell PA with a second lower high at resistance.

## Risk and Exit

- Minimum trade quality: RR must be at least 1:3.
- SL must sit behind invalidation, not at an arbitrary tight distance.
- TP1 goes to nearest internal liquidity or prior high/low.
- TP2 goes to external liquidity, H4 opposing zone, or major HTF target.
- If price reaches a meaningful profit buffer, move to breakeven only when structure supports it.
- If SL is hit, exit immediately.

## No-Trade Filters

- RR below 1:3.
- HTF bias conflicts with the LTF entry.
- Sweep happens but price does not close back into range.
- Entry depends on a subjective zone that cannot be repeated in backtest.
- News or event risk makes spread and slippage abnormal.
