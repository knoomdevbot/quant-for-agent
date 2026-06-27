# qfa Paper Trading Start — 2026-06-26

## Summary
- Account: Alpaca paper account, equity observed approximately $93.8k.
- Active-count cap from fund size: 5; selected 3 active qfa registry alphas after the initial buying-power failure.
- qfa registry active allocation total: 60%.
- Data feed: configured paper-data access used an alternate feed because recent SIP data was forbidden by the Alpaca subscription.
- Operational note: at the time of this report, local qfa runtime changes were used to test feed handling and longer daemon lookback; those source changes are not part of this research-results commit.

## Active qfa Registry
- `tsmom-voltarget-liquid-etf-randomcost-v1`: allocation 30%; symbols SPY, QQQ, IWM, TLT, GLD, SLV, USO, FXE, FXY.
- `turn-month-calendar-window-etf-v1`: allocation 15%; symbols SPY, QQQ, IWM, TLT, GLD.
- `closing-volume-reversal-costaware-megacap-v1`: allocation 15%; symbols AAPL, MSFT, NVDA, AMZN, META, GOOGL, AVGO, TSLA, JPM, LLY.

## Initial Paper Orders Placed
qfa paper orders were submitted at approximately 2026-06-26 16:30 UTC. The qfa trade_events table recorded non-dry-run events for:
- `tsmom-voltarget-liquid-etf-randomcost-v1`: SPY, QQQ, IWM, USO buys.
- `turn-month-calendar-window-etf-v1`: SPY, QQQ, IWM, TLT, GLD buys.

A second attempted paper tick after reducing registry allocations placed an additional SPY buy before failing.

## Blocker / Failure
A continuous paper daemon was attempted but exited with Alpaca paper API error:
- insufficient Reg-T buying power.

The rejected sleeve was `xsec-etf-defensive-rotation-costmonthly-v1`; it was removed from the active qfa registry after the buying-power failure.

## Current Operating State
- No qfa daemon process is currently running.
- qfa registry is populated for active paper portfolio candidates.
- Initial paper positions were opened, but ongoing automated trading is not active because of buying-power constraints and qfa daemon order semantics.

## Risks / Notes
- The current qfa daemon submits signal notionals on each tick; it is not yet a target-position rebalancer. Running it frequently can duplicate buys/sells.
- Existing Alpaca paper positions outside qfa affected Reg-T buying power.
- Before enabling recurring paper ticks, either free paper buying power or implement/verify target-rebalance semantics in qfa.
