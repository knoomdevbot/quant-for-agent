# AR-132 Evaluation Latest

Decision: **rejected**.

Data: qfa/Alpaca real daily OHLCV through configured paper-data access; no CSV, no `--data-csv`, no daemon, no orders.

Primary 10 bps full-period Sharpe: -0.97685593; ann return -0.03287934; ann vol 0.03364555; max drawdown -0.22866726; turnover 59.51290782; activation 0.29787234.

Random windows: median Sharpe -1.0045856, p25 -1.60790097, worst -2.94216707, mean -0.97360902, positive-window rate 0.2.

20 bps sensitivity full-period Sharpe: -2.67529997.

Ablations/placebos are summarized in latest.json. Orthogonality: deferred_due_rejection because Primary falsifiers were decisive before expensive alpha-library orthogonality; no child spawned.
