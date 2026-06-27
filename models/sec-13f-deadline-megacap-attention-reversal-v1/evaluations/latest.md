# AR-130 evaluation latest

Decision: **rejected**.

Primary 13F-deadline residual reversal at 10 bps one-way: Sharpe 0.354903, annualized return 0.008472, vol 0.024614, max drawdown -0.050913, activation 0.036021, average daily turnover 0.024014, event count 25, event hit rate 0.52.

Random/event-containing windows: median Sharpe 0.100233, p25 -0.751899, worst -2.185575, positive-window rate 0.566667 over 60 windows.

Key falsifiers: matched placebo Sharpe -0.71569; shifted +10td Sharpe -0.44974; generic daily residual reversal Sharpe -1.581976; generic abnormal-volume close-location reversal Sharpe -2.711475; raw pressure/no sector residual Sharpe 0.300219 with correlation 0.973612.

Conclusion: rejected because the event-gated signal had materially negative p25/worst window Sharpe, did not meet event-hit/cost robustness requirements, and was highly redundant with raw pressure reversal despite beating simple placebo/generic daily reversal proxies.
