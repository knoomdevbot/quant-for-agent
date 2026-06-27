from __future__ import annotations

import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from quant_for_agent.alpha import AlphaContext, load_alpha_function, normalize_weights
from quant_for_agent.alpaca_client import AlpacaGateway
from quant_for_agent.backtest import BacktestConfig, calculate_metrics, run_backtest
from quant_for_agent.storage import Store

REPO = Path('/Users/moonk/quant-for-agent')
MODEL_DIR = REPO / 'models' / 'meanrev-zscore-liquid-etf-regime-cost-v1'
MODEL_PATH = MODEL_DIR / 'model.py'
EVAL_DIR = MODEL_DIR / 'evaluations'
RUNS_DIR = EVAL_DIR / 'runs'
SYMBOLS = ['SPY', 'QQQ', 'IWM', 'TLT', 'GLD', 'SLV', 'XLF', 'XLK', 'XLE', 'XLV']
INITIAL_CASH = 100000.0
COST_BPS = 5.0
COST_RATE = COST_BPS / 10000.0
RANDOM_SEED = 11011
RANDOM_WINDOW_COUNT = 30
RANDOM_WINDOW_DAYS = 252
DATA_START = '2019-01-01'
DATA_END = '2025-12-31'
PRIMARY_START = '2024-01-01'
PRIMARY_END = '2025-12-31'
CLI_JSON_PATH = Path(os.environ.get('QFA_AR011_CLI_JSON', '/tmp/qfa_ar011_cli_output.json'))
QFA_DB_PATH = Path(os.environ.get('QFA_AR011_DB_PATH', '/tmp/qfa_ar011_unset.sqlite'))
QFA_RUN_ID = int(os.environ.get('QFA_AR011_RUN_ID', '1'))


def rounded_metrics(metrics):
    out = {}
    for key, value in metrics.items():
        if isinstance(value, (float, np.floating)):
            out[key] = round(float(value), 8)
        elif isinstance(value, (int, np.integer)):
            out[key] = int(value)
        else:
            out[key] = value
    return out


def compact_qfa_result(result):
    return {
        'id': result.get('id'),
        'model_path': result.get('model_path'),
        'symbols': result.get('symbols'),
        'start': result.get('start'),
        'end': result.get('end'),
        'timeframe': result.get('timeframe'),
        'initial_cash': result.get('initial_cash'),
        'metrics': rounded_metrics(result.get('metrics', {})),
    }


def detailed_eval(prices, start, end):
    model_fn = load_alpha_function(MODEL_PATH)
    px = prices.copy()
    px['timestamp'] = pd.to_datetime(px['timestamp'], utc=True)
    start_ts = pd.Timestamp(start, tz='UTC')
    end_ts = pd.Timestamp(end, tz='UTC')
    px = px[(px['symbol'].isin(SYMBOLS)) & (px['timestamp'] >= start_ts) & (px['timestamp'] <= end_ts)].sort_values(['timestamp', 'symbol'])
    close = px.pivot(index='timestamp', columns='symbol', values='close').ffill().dropna()
    rets = close.pct_change().fillna(0.0)

    equity_pre = INITIAL_CASH
    equity_cost = INITIAL_CASH
    returns_pre = []
    returns_cost = []
    curve_pre = []
    curve_cost = []
    prev_weights = {symbol: 0.0 for symbol in SYMBOLS}
    turnovers = []
    active_days = 0

    for idx, as_of in enumerate(close.index[:-1]):
        hist = px[px['timestamp'] <= as_of]
        context = AlphaContext(symbols=SYMBOLS, prices=hist, as_of=as_of)
        weights = normalize_weights(model_fn(context) or {}, SYMBOLS)
        turnover = sum(abs(weights[s] - prev_weights.get(s, 0.0)) for s in SYMBOLS)
        turnovers.append(turnover)
        if sum(abs(weights[s]) for s in SYMBOLS) > 0:
            active_days += 1
        next_ret = rets.iloc[idx + 1]
        gross_ret = sum(weights[s] * float(next_ret.get(s, 0.0)) for s in SYMBOLS)
        cost_ret = gross_ret - turnover * COST_RATE
        equity_pre *= (1.0 + gross_ret)
        equity_cost *= (1.0 + cost_ret)
        returns_pre.append(gross_ret)
        returns_cost.append(cost_ret)
        curve_pre.append({'timestamp': close.index[idx + 1].isoformat(), 'equity': equity_pre})
        curve_cost.append({'timestamp': close.index[idx + 1].isoformat(), 'equity': equity_cost})
        prev_weights = weights

    metrics_pre = calculate_metrics(INITIAL_CASH, equity_pre, returns_pre, curve_pre)
    metrics_cost = calculate_metrics(INITIAL_CASH, equity_cost, returns_cost, curve_cost)
    avg_turnover = float(np.mean(turnovers)) if turnovers else 0.0
    total_turnover = float(np.sum(turnovers)) if turnovers else 0.0
    return {
        'start': start,
        'end': end,
        'periods': int(len(returns_pre)),
        'metrics_pre_cost': rounded_metrics(metrics_pre),
        'metrics_cost_adjusted': rounded_metrics(metrics_cost),
        'turnover': {
            'average_daily_one_way_notional': round(avg_turnover, 8),
            'total_one_way_notional': round(total_turnover, 8),
            'active_days': int(active_days),
            'active_day_fraction': round(float(active_days / len(returns_pre)), 8) if returns_pre else 0.0,
        },
        'equity_curve_cost_adjusted_tail': [
            {'timestamp': p['timestamp'], 'equity': round(float(p['equity']), 4)} for p in curve_cost[-5:]
        ],
    }


def spy_baseline(prices, start, end):
    px = prices.copy()
    px['timestamp'] = pd.to_datetime(px['timestamp'], utc=True)
    s = px[(px['symbol'] == 'SPY') & (px['timestamp'] >= pd.Timestamp(start, tz='UTC')) & (px['timestamp'] <= pd.Timestamp(end, tz='UTC'))].sort_values('timestamp')
    close = s.set_index('timestamp')['close'].ffill().dropna()
    arr = close.pct_change().fillna(0.0).iloc[1:].tolist()
    equity = INITIAL_CASH
    curve = []
    for ts, ret in zip(close.index[1:], arr):
        equity *= (1.0 + float(ret))
        curve.append({'timestamp': ts.isoformat(), 'equity': equity})
    return rounded_metrics(calculate_metrics(INITIAL_CASH, equity, arr, curve))


def sample_windows(prices):
    close = prices.pivot(index='timestamp', columns='symbol', values='close').ffill().dropna()
    dates = list(pd.to_datetime(close.index, utc=True))
    max_start = len(dates) - RANDOM_WINDOW_DAYS - 1
    rng = random.Random(RANDOM_SEED)
    starts = sorted(rng.sample(range(0, max_start), RANDOM_WINDOW_COUNT))
    return [
        {'window_id': i, 'start': dates[idx].strftime('%Y-%m-%d'), 'end': dates[idx + RANDOM_WINDOW_DAYS].strftime('%Y-%m-%d')}
        for i, idx in enumerate(starts, 1)
    ]


def summarize_random(runs):
    fields = ['sharpe', 'annualized_return', 'annualized_volatility', 'max_drawdown', 'win_rate', 'total_return', 'periods']
    summary = {}
    for prefix in ['metrics_pre_cost', 'metrics_cost_adjusted']:
        summary[prefix] = {}
        for field in fields:
            vals = [r[prefix][field] for r in runs]
            summary[prefix][field] = {
                'median': round(float(np.median(vals)), 8),
                'mean': round(float(np.mean(vals)), 8),
                'min': round(float(np.min(vals)), 8),
                'max': round(float(np.max(vals)), 8),
            }
    summary['turnover'] = {
        'median_average_daily_one_way_notional': round(float(np.median([r['turnover']['average_daily_one_way_notional'] for r in runs])), 8),
        'mean_average_daily_one_way_notional': round(float(np.mean([r['turnover']['average_daily_one_way_notional'] for r in runs])), 8),
        'median_active_day_fraction': round(float(np.median([r['turnover']['active_day_fraction'] for r in runs])), 8),
    }
    return summary


def read_cli_result():
    if CLI_JSON_PATH.exists():
        return json.loads(CLI_JSON_PATH.read_text(encoding='utf-8'))
    if QFA_DB_PATH.exists():
        result = Store(QFA_DB_PATH).get_backtest(QFA_RUN_ID)
        if result:
            result['id'] = QFA_RUN_ID
            return result
    return None


def main():
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    gateway = AlpacaGateway()
    prices = gateway.get_bars(SYMBOLS, start=DATA_START, end=DATA_END, timeframe='1Day')
    prices['timestamp'] = pd.to_datetime(prices['timestamp'], utc=True)

    qfa_cli_result = read_cli_result()
    primary_config = BacktestConfig(model_path=str(MODEL_PATH), symbols=SYMBOLS, start=PRIMARY_START, end=PRIMARY_END, timeframe='1Day', initial_cash=INITIAL_CASH)
    qfa_direct_result = run_backtest(primary_config, prices)
    qfa_direct_result['id'] = 'direct_python_qfa_engine_no_store'

    primary_detail = detailed_eval(prices, PRIMARY_START, PRIMARY_END)
    random_runs = []
    for window in sample_windows(prices):
        result = detailed_eval(prices, window['start'], window['end'])
        result['window_id'] = window['window_id']
        random_runs.append(result)
    random_summary = summarize_random(random_runs)
    benchmark = spy_baseline(prices, PRIMARY_START, PRIMARY_END)

    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    immutable_name = f"qfa_real_alpaca_ar011_{created_at.replace(':', '').replace('-', '').replace('Z', 'Z')}.json"
    run_path = RUNS_DIR / immutable_name

    decision = 'rejected'
    decision_reason = 'Median random-window Sharpe after 5 bps one-way turnover cost is <= 0, failing AR-011 falsifier.'
    if random_summary['metrics_cost_adjusted']['sharpe']['median'] > 0 and primary_detail['metrics_cost_adjusted']['max_drawdown'] > -0.15:
        decision = 'watchlist'
        decision_reason = 'Positive random-window median Sharpe after cost and primary drawdown under 15%; keep on watchlist pending richer execution-cost validation.'

    qfa_command = (
        'set -a; source /Users/moonk/.hermes/profiles/alphaaoi/secrets/alpaca.env; set +a; '
        'export ALPACA_API_KEY="${ALPACA_API_KEY:-${ALPACA_KEY_ID:-}}"; export ALPACA_PAPER=true; '
        '/Users/moonk/quant-for-agent/.venv/bin/qfa backtest run '
        '/Users/moonk/quant-for-agent/models/meanrev-zscore-liquid-etf-regime-cost-v1/model.py '
        '--symbols SPY,QQQ,IWM,TLT,GLD,SLV,XLF,XLK,XLE,XLV --start 2024-01-01 --end 2025-12-31 '
        '--timeframe 1Day --initial-cash 100000 --db <temporary-sqlite-db>'
    )
    artifact_command = (
        'set -a; source /Users/moonk/.hermes/profiles/alphaaoi/secrets/alpaca.env; set +a; '
        'export ALPACA_API_KEY="${ALPACA_API_KEY:-${ALPACA_KEY_ID:-}}"; export ALPACA_PAPER=true; '
        'QFA_AR011_DB_PATH=<temporary-sqlite-db> QFA_AR011_CLI_JSON=/tmp/qfa_ar011_cli_output.json '
        '/Users/moonk/quant-for-agent/.venv/bin/python /Users/moonk/quant-for-agent/models/meanrev-zscore-liquid-etf-regime-cost-v1/evaluate_ar011.py'
    )

    run_payload = {
        'created_at': created_at,
        'issue_id': 'AR-011',
        'model_name': 'meanrev-zscore-liquid-etf-regime-cost-v1',
        'data_source': 'Alpaca real daily market data via qfa AlpacaGateway; no CSV; no --data-csv',
        'symbols': SYMBOLS,
        'date_ranges': {'data_fetch': {'start': DATA_START, 'end': DATA_END}, 'primary': {'start': PRIMARY_START, 'end': PRIMARY_END}},
        'qfa_cli_run': compact_qfa_result(qfa_cli_result) if qfa_cli_result else None,
        'qfa_direct_engine_run': compact_qfa_result(qfa_direct_result),
        'primary_cost_adjusted_detail': primary_detail,
        'spy_benchmark_primary': benchmark,
        'random_window_protocol': {'seed': RANDOM_SEED, 'count': RANDOM_WINDOW_COUNT, 'window_trading_days': RANDOM_WINDOW_DAYS, 'summary': random_summary, 'runs': random_runs},
    }
    run_path.write_text(json.dumps(run_payload, indent=2, sort_keys=True), encoding='utf-8')

    latest = {
        'created_at': created_at,
        'issue_id': 'AR-011',
        'model_name': 'meanrev-zscore-liquid-etf-regime-cost-v1',
        'evaluation_status': 'completed_real_data_backtest',
        'data_source': 'Alpaca real daily market data via qfa CLI and qfa AlpacaGateway; no CSV; no --data-csv',
        'no_csv_used': True,
        'daemon_used': False,
        'trades_placed': False,
        'symbols': SYMBOLS,
        'date_ranges': {'full_data': {'start': DATA_START, 'end': DATA_END}, 'primary': {'start': PRIMARY_START, 'end': PRIMARY_END}},
        'commands': {'qfa_primary_cli': qfa_command, 'artifact_generation': artifact_command},
        'qfa_db': {'path_used_during_run': str(QFA_DB_PATH), 'db_artifact_retained': False},
        'qfa_run_ids': {'cli_primary': QFA_RUN_ID if qfa_cli_result else None, 'direct_engine_primary': 'direct_python_qfa_engine_no_store'},
        'artifacts': {'latest_json': str(EVAL_DIR / 'latest.json'), 'latest_md': str(EVAL_DIR / 'latest.md'), 'immutable_run_json': str(run_path)},
        'metrics': {
            'primary_qfa_pre_cost': rounded_metrics((qfa_cli_result or qfa_direct_result)['metrics']),
            'primary_external_cost_adjusted_5bps_one_way': primary_detail['metrics_cost_adjusted'],
            'primary_turnover': primary_detail['turnover'],
            'spy_benchmark_primary': benchmark,
            'random_windows_summary': random_summary,
        },
        'orthogonality': {'status': 'unavailable', 'reason': 'No canonical accepted-alpha return stream or orthogonality harness exists in this repository for AR-011 comparison.'},
        'costs_slippage': {'assumption_one_way_bps': COST_BPS, 'qfa_cli_costs_applied': False, 'external_cost_postprocess_applied': True, 'method': 'daily target-weight turnover haircut: cost_return = gross_return - sum(abs(delta_weight))*0.0005'},
        'suggested_decision': decision,
        'decision_reason': decision_reason,
        'refinement_child_idea': {'id': 'AR-011-R1', 'title': 'Long-only oversold ETF rebound with adaptive volatility cutoff', 'hypothesis': 'Remove short legs and allow cash during high-volatility regimes to preserve rebound exposure while reducing turnover and trend-fighting losses.'},
        'divergent_child_idea': {'id': 'AR-011-D1', 'title': 'Cross-sectional ETF dispersion convergence after macro shock days', 'hypothesis': 'Trade sector/asset-class ETF residual dispersion convergence after large SPY/TLT/GLD disagreement days instead of time-series z-score reversal.'},
        'warnings': ['qfa CLI metrics are pre-cost; 5 bps one-way costs are applied externally.', 'Evaluation is close-to-close on daily bars and excludes bid/ask spread dynamics, market impact, borrow/short availability, and intraday fill timing.'],
    }
    (EVAL_DIR / 'latest.json').write_text(json.dumps(latest, indent=2, sort_keys=True), encoding='utf-8')

    md = f"""# AR-011 Evaluation — meanrev-zscore-liquid-etf-regime-cost-v1

## Suggested decision

**{decision.upper()}** — {decision_reason}

## Data and commands

- Data source: Alpaca real daily market data via qfa CLI and qfa `AlpacaGateway`; no CSV and no `--data-csv`.
- Symbols: {', '.join(SYMBOLS)}.
- Primary window: {PRIMARY_START} to {PRIMARY_END}; random protocol uses 30 sampled 252-trading-day windows from {DATA_START} to {DATA_END}.
- qfa DB used during run: `{QFA_DB_PATH}`; DB artifact retained: `false`.
- qfa primary run id: `{QFA_RUN_ID if qfa_cli_result else 'unavailable'}`.
- Immutable run JSON: `{run_path}`.

## Primary metrics

- qfa/pre-cost total return: `{(qfa_cli_result or qfa_direct_result)['metrics']['total_return']:.4f}`.
- qfa/pre-cost annualized return: `{(qfa_cli_result or qfa_direct_result)['metrics']['annualized_return']:.4f}`.
- qfa/pre-cost Sharpe: `{(qfa_cli_result or qfa_direct_result)['metrics']['sharpe']:.4f}`.
- qfa/pre-cost max drawdown: `{(qfa_cli_result or qfa_direct_result)['metrics']['max_drawdown']:.4f}`.
- qfa/pre-cost win rate: `{(qfa_cli_result or qfa_direct_result)['metrics']['win_rate']:.4f}`.
- qfa/pre-cost periods: `{(qfa_cli_result or qfa_direct_result)['metrics']['periods']}`.
- Cost-adjusted Sharpe, 5 bps one-way: `{primary_detail['metrics_cost_adjusted']['sharpe']:.4f}`.
- Cost-adjusted annualized return: `{primary_detail['metrics_cost_adjusted']['annualized_return']:.4f}`.
- Cost-adjusted max drawdown: `{primary_detail['metrics_cost_adjusted']['max_drawdown']:.4f}`.
- Cost-adjusted win rate: `{primary_detail['metrics_cost_adjusted']['win_rate']:.4f}`.
- Average daily one-way turnover proxy: `{primary_detail['turnover']['average_daily_one_way_notional']:.6f}`.

## Random-window results

- Median random-window pre-cost Sharpe: `{random_summary['metrics_pre_cost']['sharpe']['median']:.4f}`.
- Median random-window cost-adjusted Sharpe: `{random_summary['metrics_cost_adjusted']['sharpe']['median']:.4f}`.
- Median random-window cost-adjusted annualized return: `{random_summary['metrics_cost_adjusted']['annualized_return']['median']:.4f}`.
- Median random-window cost-adjusted max drawdown: `{random_summary['metrics_cost_adjusted']['max_drawdown']['median']:.4f}`.
- Median random-window cost-adjusted win rate: `{random_summary['metrics_cost_adjusted']['win_rate']['median']:.4f}`.

## Orthogonality

Unavailable: no canonical accepted-alpha return stream or orthogonality harness exists in this repository for AR-011 comparison.

## Child ideas

- Refinement: **AR-011-R1 — Long-only oversold ETF rebound with adaptive volatility cutoff.** Remove short legs and allow cash during high-volatility regimes to reduce trend-fighting losses.
- Divergent: **AR-011-D1 — Cross-sectional ETF dispersion convergence after macro shock days.** Trade residual ETF dispersion convergence after large SPY/TLT/GLD disagreement days.

## Warnings

- qfa CLI metrics are pre-cost; this evaluation applies a separate 5 bps one-way turnover haircut.
- Daily close-to-close proxy excludes bid/ask spread dynamics, market impact, borrow/short availability, ETF liquidity microstructure, and intraday fill timing.
"""
    (EVAL_DIR / 'latest.md').write_text(md, encoding='utf-8')

    print(json.dumps({'latest_json': str(EVAL_DIR / 'latest.json'), 'latest_md': str(EVAL_DIR / 'latest.md'), 'run_json': str(run_path), 'decision': decision, 'primary_cost_adjusted_sharpe': primary_detail['metrics_cost_adjusted']['sharpe'], 'median_random_cost_adjusted_sharpe': random_summary['metrics_cost_adjusted']['sharpe']['median']}, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
