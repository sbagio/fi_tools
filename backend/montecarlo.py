# backend/montecarlo.py

import yfinance as yf
import numpy as np
import pandas as pd

def run_monte_carlo_simulation(
    tickers,
    weights,
    initial_investment,
    start_date,
    end_date,
    years,
    n_sims=10_000,
    portfolio_std_est=0.28,
):
    """
    Performs a simplified Monte Carlo simulation using 'Close' prices for
    each ticker in yfinance.

    Parameters
    ----------
    tickers : list of str
        Example: ["VGT", "SMH", "MGK", "QQQM"].
    weights : list of float
        Portfolio weights for each ticker; should sum to ~1.0.
    initial_investment : float
        The starting amount of money, e.g., 800_000.0.
    start_date : str
        Start date (e.g., "2013-01-01") for retrieving data from yfinance.
    end_date : str
        End date (e.g., "2023-01-01") for retrieving data from yfinance.
    years : int
        Number of years to simulate forward (e.g., 5).
    n_sims : int, optional
        Number of simulation iterations, default 10,000.
    portfolio_std_est : float, optional
        Approx. annual standard deviation for the entire portfolio (e.g., 0.28).

    Returns
    -------
    dict
        {
            "pct_25": 25th percentile of final values,
            "pct_50": 50th percentile (median),
            "pct_75": 75th percentile,
            "mean": arithmetic mean of final values,
            "all_final_values": list of all simulated final values
        }
    """

    # 1) Download historical data using 'Close'
    raw_data = yf.download(tickers, start=start_date, end=end_date)

    # If multi-index, "Close" might be at raw_data["Close"]
    # or if single-level, just raw_data["Close"]. 
    # We'll handle both cases:
    if "Close" in raw_data.columns:
        # Single-level columns: we can directly select "Close"
        data = raw_data["Close"].dropna()
    else:
        # Possibly multi-index (like raw_data["Close", ticker])
        # We select the cross-section of 'Close'
        data = raw_data.xs("Close", axis=1, level=0, drop_level=False).dropna()

    # 2) Calculate daily returns, then annualize 
    daily_returns = data.pct_change().dropna(how="all")
    trading_days_per_year = 252

    # Weighted average annual return
    avg_annual_returns = []
    for t in tickers:
        # daily_returns[t] might be a single Series if single-level,
        # or we might need daily_returns[(t, )] if multi-level.
        # Usually if single-level, columns are just ['VGT', 'SMH', ...].
        # If multi-level, they'd be something like [('Close','VGT'), ...].
        # We'll try straightforward indexing first:
        try:
            mean_daily_ret = daily_returns[t].mean()
        except KeyError:
            # multi-level scenario: daily_returns[('Close', t)]
            mean_daily_ret = daily_returns[("Close", t)].mean()
        mean_annual_ret = (1 + mean_daily_ret) ** trading_days_per_year - 1
        avg_annual_returns.append(mean_annual_ret)

    portfolio_mean_return = sum(w * r for w, r in zip(weights, avg_annual_returns))

    # 3) Monte Carlo simulation (lognormal approach)
    mu_log = np.log(1 + portfolio_mean_return)
    sigma_log = portfolio_std_est

    rng = np.random.default_rng(seed=None)
    final_values_list = []

    for _ in range(n_sims):
        total_growth = 1.0
        for _year in range(years):
            log_ret = rng.normal(mu_log, sigma_log)
            annual_factor = np.exp(log_ret)
            total_growth *= annual_factor
        final_values_list.append(initial_investment * total_growth)

    final_values = np.array(final_values_list)

    # 4) Return quartiles, mean, and all values
    results = {
        "pct_25": float(np.percentile(final_values, 25)),
        "pct_50": float(np.percentile(final_values, 50)),
        "pct_75": float(np.percentile(final_values, 75)),
        "mean": float(np.mean(final_values)),
        "all_final_values": final_values.tolist(),
    }

    return results
