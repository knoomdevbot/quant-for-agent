# tic-foreign-treasury-flow-pressure-etf-scout-v1

## Hypothesis

Timestamp-safe monthly Treasury International Capital (TIC) foreign Treasury/security flow pressure might predict next-month duration, USD, gold, or credit ETF pressure after the official release lag.

## Signal Definition

The recovered evaluation parsed official dated Treasury TIC monthly release ZIP archives where available and constructed a foreign Treasury flow-pressure composite. Trading was modeled no earlier than the first ETF trading session after the public 4 p.m. ET release date.

## Evaluation Summary

Decision: **rejected**.

- Source/vintage gate: passed for a limited 2021+ archive subset, with 33 parsed releases and 22 signal-bearing releases.
- Full-sample 10 bps Sharpe: -0.587.
- Random windows: median Sharpe -0.511, p25 -0.852, worst -2.464, positive-window rate 25.5%.
- Max drawdown: -12.4%.
- Primary controls/static ETF baselines dominated; inverted signal was materially better than the proposed direction.

## Orthogonality / Redundancy

The candidate was not accepted. Orthogonality was used as a rejection/control diagnostic rather than a promotion argument. Max absolute control correlation was ~0.989 versus the inverted signal, and static ETF controls dominated return quality.

## Known Risks

- Monthly TIC data are stale and revision/benchmark-survey-sensitive.
- The parsed source-vintage overlap was short.
- Public real market prices were transient and compact summaries only were retained.
- No raw TIC ZIPs, raw bars, equity curves, daemon state, orders, or database files are retained.

## Change Log

- 2026-06-29: Timeout recovery kept compact rejected evaluation artifacts and added qfa-compatible zero-weight model wrapper.
