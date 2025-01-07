import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def get_historical_data(tickers, years=10):
    """Fetch historical data for the given tickers."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years*365)
    
    data = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)
            data[ticker] = hist['Close']
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
    
    return pd.DataFrame(data)

def calculate_metrics(df):
    """Calculate annual returns and volatilities."""
    # Calculate daily returns
    daily_returns = df.pct_change().dropna()
    
    # Calculate annual metrics
    annual_returns = {}
    annual_volatilities = {}
    
    for column in daily_returns.columns:
        # Annualized return (geometric mean)
        annual_returns[column] = (1 + daily_returns[column]).prod() ** (252/len(daily_returns)) - 1
        
        # Annualized volatility
        annual_volatilities[column] = daily_returns[column].std() * np.sqrt(252)
    
    return annual_returns, annual_volatilities

# Portfolio configuration
initial_value = 800000
holdings = {
    'VGT': 0.25,
    'SMH': 0.15,
    'MGK': 0.15,
    'QQQM': 0.20,
    'BRKB': 0.10,
    'TQQQ': 0.05,
    'USD': 0.05,    # ProShares Ultra Semiconductors
    'TECL': 0.05
}

# Fetch historical data
print("Fetching historical data...")
historical_data = get_historical_data(holdings.keys())
returns, volatility = calculate_metrics(historical_data)

def run_simulation(num_simulations=10000, years=5):
    portfolio_returns = []
    
    for _ in range(num_simulations):
        value = initial_value
        
        for _ in range(years):
            annual_return = 0
            
            for asset, weight in holdings.items():
                mu = np.log(1 + returns[asset]) - 0.5 * volatility[asset]**2
                sigma = volatility[asset]
                random_return = np.random.lognormal(mu, sigma) - 1
                annual_return += random_return * weight
            
            value *= (1 + annual_return)
        
        portfolio_returns.append(value)
    
    return np.array(portfolio_returns)

print("\nRunning Monte Carlo simulation...")
results = run_simulation()

# Calculate statistics
percentiles = np.percentile(results, [25, 50, 75])
mean_value = np.mean(results)
std_dev = np.std(results)
var_95 = np.percentile(results, 5)

# Print detailed results
print("\nPortfolio Analysis Results")
print("=" * 50)
print(f"Initial Investment: ${initial_value:,.2f}")
print("\nHistorical Metrics (Annualized):")
print("-" * 30)
for asset in holdings.keys():
    print(f"{asset}:")
    print(f"  Return: {returns[asset]:,.2%}")
    print(f"  Volatility: {volatility[asset]:,.2%}")

print("\nSimulation Results (5-Year Horizon):")
print("-" * 30)
print(f"25th Percentile: ${percentiles[0]:,.2f}")
print(f"Median (50th): ${percentiles[1]:,.2f}")
print(f"75th Percentile: ${percentiles[2]:,.2f}")
print(f"Mean: ${mean_value:,.2f}")
print(f"Standard Deviation: ${std_dev:,.2f}")
print(f"95% VaR: ${var_95:,.2f}")