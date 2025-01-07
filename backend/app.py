# backend/app.py

import datetime
import pandas as pd
import yfinance as yf
import traceback

from flask import Flask, request, jsonify
from flask_cors import CORS

from montecarlo import run_monte_carlo_simulation

app = Flask(__name__)
CORS(app)

@app.route("/tickerinfo", methods=["POST"])
def tickerinfo():
    """
    Expects a JSON payload: { "ticker": "VGT" }
    Returns JSON with fields:
      {
        "ticker": "...",
        "fullName": "...",
        "currentPrice": 123.45,
        "annualDividendYield": 0.015,    # e.g., 1.5%
        "expenseRatio": 0.001,          # e.g., 0.1%
        "past12MoReturn": 0.18,         # e.g., 18%
        "tenYearReturn": 0.20,          # e.g., 20%
        "tenYearStart": "YYYY-MM-DD" or null
      }
    """

    data = request.json
    ticker = data.get("ticker", "").upper().strip()
    if not ticker:
        return jsonify({"error": "No ticker provided"}), 400

    try:
        # Download ~10 years of daily data from yfinance
        end_date_dt = datetime.date.today()
        start_date_dt = end_date_dt.replace(year=end_date_dt.year - 10)

        df = yf.download(ticker, start=start_date_dt, end=end_date_dt)
        if df.empty:
            return jsonify({"error": f"No data found for ticker {ticker}"}), 404

        # -----------------------
        # GET CURRENT PRICE
        # -----------------------
        if "Close" in df.columns:
            # Single-level columns
            last_close = df["Close"].iloc[-1]
        else:
            # Multi-level columns => cross-section "Close"
            df_close = df.xs("Close", axis=1, level=0, drop_level=False)
            last_close = df_close.iloc[-1]

        if isinstance(last_close, pd.Series):
            # if still a one-element Series, pick that element
            last_close = last_close.iloc[0]

        current_price = float(last_close)

        # -----------------------
        # GET LONG NAME
        # -----------------------
        info = yf.Ticker(ticker).info
        long_name = info.get("longName") or info.get("shortName") or ticker

        # -----------------------
        # EXPENSE RATIO
        # -----------------------
        expense_ratio = info.get("expenseRatio", 0.0)  # e.g. 0.001 => 0.1%

        # -----------------------
        # DIVIDEND YIELD
        # -----------------------
        dividends = yf.Ticker(ticker).dividends
        annual_div_yield = 0.0
        if not dividends.empty:
            one_year_ago = pd.Timestamp.now() - pd.DateOffset(years=1)
            recent_divs = dividends[dividends.index >= one_year_ago]
            total_divs = recent_divs.sum()
            annual_div_yield = float(total_divs / current_price)

        # -----------------------
        # PAST 12 MO RETURN
        # -----------------------
        df_1y = df[df.index >= (pd.Timestamp.now() - pd.DateOffset(years=1))]
        if not df_1y.empty:
            first_price_1y = df_1y["Close"].iloc[0]
            if isinstance(first_price_1y, pd.Series):
                first_price_1y = first_price_1y.iloc[0]
            past12MoReturn = (current_price - float(first_price_1y)) / float(first_price_1y)
        else:
            past12MoReturn = 0.0

        # -----------------------
        # 10-YEAR RETURN or PARTIAL
        # -----------------------
        first_date = df.index[0]
        years_of_data = (df.index[-1] - df.index[0]).days / 365.0

        ten_year_return = None
        ten_year_start = None

        if years_of_data >= 9.5:
            first_close = df["Close"].iloc[0]
            if isinstance(first_close, pd.Series):
                first_close = first_close.iloc[0]
            total_return_factor = current_price / float(first_close)
            annualized = total_return_factor ** (1.0 / years_of_data) - 1.0
            ten_year_return = float(annualized)
        else:
            ten_year_start = str(first_date.date())

        # -----------------------
        # BUILD RESPONSE
        # -----------------------
        result = {
            "ticker": ticker,
            "fullName": long_name,
            "currentPrice": current_price,
            "annualDividendYield": annual_div_yield,
            "expenseRatio": float(expense_ratio),
            "past12MoReturn": float(past12MoReturn),
            "tenYearReturn": ten_year_return,   # or None
            "tenYearStart": ten_year_start      # or None
        }

        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/simulate", methods=["POST"])
def simulate():
    """
    This route now REQUIRES user-provided 'tickers' and 'weights' 
    in the JSON. No default tickers/weights are used. 

    Example expected input payload:
    {
      "tickers": ["VGT", "SMH", "MGK"],
      "weights": [0.40, 0.35, 0.25],
      "initial_investment": 500000,
      "years": 5,
      "n_sims": 10000,
      "portfolio_std_est": 0.28
    }
    """

    data = request.json

    # 1) Validate that tickers & weights are provided
    if "tickers" not in data or "weights" not in data:
        return jsonify({"error": "No tickers or weights provided"}), 400

    tickers = data["tickers"]
    weights = data["weights"]

    # Extra check: arrays have same length
    if len(tickers) != len(weights):
        return jsonify({"error": "Length mismatch between tickers and weights"}), 400

    initial_investment = data.get("initial_investment", 800_000.0)
    years = data.get("years", 5)
    n_sims = data.get("n_sims", 10_000)
    portfolio_std_est = data.get("portfolio_std_est", 0.28)

    # automatically fetch 10 years of data
    end_date_dt = datetime.date.today()
    start_date_dt = end_date_dt.replace(year=end_date_dt.year - 10)

    end_date = end_date_dt.strftime("%Y-%m-%d")
    start_date = start_date_dt.strftime("%Y-%m-%d")

    # Run the Monte Carlo simulation
    results = run_monte_carlo_simulation(
        tickers=tickers,
        weights=weights,
        initial_investment=initial_investment,
        start_date=start_date,
        end_date=end_date,
        years=years,
        n_sims=n_sims,
        portfolio_std_est=portfolio_std_est
    )

    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
