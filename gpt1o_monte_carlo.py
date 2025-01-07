import yfinance as yf
import numpy as np
import pandas as pd

# ---------------------------
# 1. USER INPUTS
# ---------------------------

# ETFs and weights (must match in length)
tickers = ["VGT", "SMH", "MGK", "QQQM", "BRK-B", "TQQQ", "USD", "TECL"]
weights = [0.25,   0.15,   0.15,   0.20,   0.10,   0.05,   0.05,   0.05]

initial_investment = 800_000.0
start_date = "2013-01-01"
end_date   = "2025-01-01"  # 10-year window (adjust as needed)

# Assume a single portfolio std dev (you might refine this)
# If you are including leveraged ETFs, consider pushing this higher
portfolio_std = 0.28  # 28% annual volatility (example)

# Number of simulation runs
n_sims = 10_000
years = 5

# ---------------------------
# 2. GET HISTORICAL DATA
# ---------------------------
# Download 'Adj Close' prices from Yahoo Finance
data = yf.download(tickers, start=start_date, end=end_date)["Adj Close"]

# Some tickers like BRK-B may need special handling in older data,
# but let's assume yfinance handles them. For "USD" (ProShares Ultra
# Semiconductors), Yahoo's ticker might be different (e.g. "USD" isn't
# standard). You can find the correct symbol, e.g. "USD" -> "USD" 
# if Yahoo supports it. Otherwise, you'll need the right symbol name.

# Drop any missing columns/rows if needed
data.dropna(axis=0, how='any', inplace=True)

# ---------------------------
# 3. CALCULATE HISTORICAL RETURNS
# ---------------------------
# We'll compute daily returns, then annualize them
daily_returns = data.pct_change().dropna()

# For each ticker, compute average daily return, then scale to annual
avg_annual_returns = {}
trading_days_per_year = 252

for t in tickers:
    # Mean daily return
    mean_daily_ret = daily_returns[t].mean()
    # Approx annual return
    mean_annual_ret = (1 + mean_daily_ret)**trading_days_per_year - 1
    avg_annual_returns[t] = mean_annual_ret

# Weighted average annual return
portfolio_mean_return = sum(w * avg_annual_returns[t] for w, t in zip(weights, tickers))

print("Approx. Annual Returns for Each Ticker:")
for t in tickers:
    print(f"{t}: {avg_annual_returns[t]:.2%}")

print(f"\nWeighted Portfolio Annual Return (historical): {portfolio_mean_return:.2%}")

# ---------------------------
# 4. SINGLE-FACTOR MONTE CARLO
# ---------------------------
# We'll model the portfolio's annual returns from a lognormal distribution
# with mean = portfolio_mean_return, std = portfolio_std, i.i.d. across years.

# Convert arithmetic mean to 'log-return' drift
mu_daily = np.log(1 + portfolio_mean_return)  # log of (1 + r)
sigma_daily = portfolio_std  # for simplicity, treat as log-return std

# We do "years" draws for each simulation path
final_values = []
rng = np.random.default_rng(seed=42)  # for reproducibility (optional)

for _ in range(n_sims):
    # Draw random annual returns from Normal(log(1+r), sigma)
    # Then exponentiate for actual growth
    total_growth = 1.0
    for _year in range(years):
        # log-return ~ Normal(mu_daily, sigma_daily)
        log_ret = rng.normal(mu_daily, sigma_daily)
        # convert log-return to multiplicative factor
        annual_factor = np.exp(log_ret)
        total_growth *= annual_factor
    
    final_values.append(initial_investment * total_growth)

final_values = np.array(final_values)

# ---------------------------
# 5. RESULTS
# ---------------------------
# Calculate percentiles
pct_25 = np.percentile(final_values, 25)
pct_50 = np.percentile(final_values, 50)
pct_75 = np.percentile(final_values, 75)
mean_val = np.mean(final_values)

print("\nMonte Carlo Results (Single-Factor Model, 5 years):")
print(f"25th percentile: ${pct_25:,.0f}")
print(f"50th percentile (median): ${pct_50:,.0f}")
print(f"75th percentile: ${pct_75:,.0f}")
print(f"Mean: ${mean_val:,.0f}")
