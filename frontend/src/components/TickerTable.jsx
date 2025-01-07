// src/components/TickerTable.jsx

import React, { useState } from "react";

/**
 * This function calls the new /tickerinfo endpoint in app.py
 * to get data about a single ticker (price, name, yield, etc.).
 */
async function fetchTickerData(ticker) {
  const res = await fetch("http://localhost:5000/tickerinfo", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ticker }),
  });
  if (!res.ok) {
    throw new Error(`Error fetching data for ticker ${ticker}`);
  }
  const data = await res.json();
  if (data.error) {
    throw new Error(data.error);
  }
  return data;
}

// Up to 15 tickers in the table
const MAX_TICKERS = 15;

// Generates an empty row object
function createEmptyRow() {
  return {
    ticker: "",
    fullName: "",
    currentPrice: null,
    annualDividendYield: null,
    expenseRatio: null,
    past12MoReturn: null,
    tenYearReturn: null,
    tenYearStart: null,
    value: 0
  };
}

export default function TickerTable({ onTableChange }) {
  const [rows, setRows] = useState([createEmptyRow()]);

  // Compute total portfolio value
  const totalValue = rows.reduce((acc, row) => acc + (row.value || 0), 0);

  // Add new row
  const handleAddRow = () => {
    if (rows.length < MAX_TICKERS) {
      setRows((prev) => [...prev, createEmptyRow()]);
    }
  };

  // Remove row
  const handleRemoveRow = (index) => {
    setRows((prev) => prev.filter((_, i) => i !== index));
  };

  // Handle user input changes for ticker or value
  const handleChange = (index, field, newValue) => {
    const updated = [...rows];
    updated[index] = { ...updated[index], [field]: newValue };
    setRows(updated);

    // Inform parent if needed
    if (onTableChange) {
      onTableChange(updated);
    }
  };

  // When user leaves the ticker field, fetch data if ticker is non-empty
  const handleTickerBlur = async (index) => {
    const row = rows[index];
    if (!row.ticker) return;

    try {
      const data = await fetchTickerData(row.ticker.trim().toUpperCase());
      // Update row with returned info
      const updated = [...rows];
      updated[index] = {
        ...row,
        ticker: data.ticker,
        fullName: data.fullName,
        currentPrice: data.currentPrice,
        annualDividendYield: data.annualDividendYield,
        expenseRatio: data.expenseRatio,
        past12MoReturn: data.past12MoReturn,
        tenYearReturn: data.tenYearReturn,
        tenYearStart: data.tenYearStart
      };
      setRows(updated);
      if (onTableChange) {
        onTableChange(updated);
      }
    } catch (error) {
      console.error("Ticker fetch error:", error.message);
      alert(`Could not fetch data for ticker '${row.ticker}': ${error.message}`);
    }
  };

  return (
    <div style={{ overflowX: "auto", marginBottom: "1rem" }}>
      <h3>Portfolio Tickers</h3>
      <table style={{ borderCollapse: "collapse", minWidth: "900px" }}>
        <thead>
          <tr>
            <th style={thStyle}>Ticker</th>
            <th style={thStyle}>Full Name</th>
            <th style={thStyle}>Current Price</th>
            <th style={thStyle}>Annual Div. Yield</th>
            <th style={thStyle}>Expense Ratio</th>
            <th style={thStyle}>Past 12mo Return</th>
            <th style={thStyle}>10yr Return</th>
            <th style={thStyle}>Value</th>
            <th style={thStyle}>% of Portfolio</th>
            <th style={thStyle}></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => {
            const {
              ticker,
              fullName,
              currentPrice,
              annualDividendYield,
              expenseRatio,
              past12MoReturn,
              tenYearReturn,
              tenYearStart,
              value
            } = row;

            // If totalValue is zero, display "0.00"
            const pctOfPortfolio = totalValue > 0 
              ? ((value / totalValue) * 100).toFixed(2) 
              : "0.00";

            // For 10yr return, if we have data, show e.g. "20.0% (since 2018-03-01)"
            let tenYearDisplay = "";
            if (tenYearReturn !== null && tenYearReturn !== undefined) {
              tenYearDisplay = (tenYearReturn * 100).toFixed(1) + "%";
              if (tenYearStart) {
                tenYearDisplay += ` (since ${tenYearStart})`;
              }
            }

            return (
              <tr key={i}>
                <td style={tdStyle}>
                  <input
                    type="text"
                    value={ticker}
                    onChange={(e) => handleChange(i, "ticker", e.target.value)}
                    onBlur={() => handleTickerBlur(i)}
                    style={{ width: "80px" }}
                  />
                </td>
                <td style={tdStyle}>{fullName || ""}</td>
                <td style={tdStyle}>
                  {currentPrice != null ? currentPrice.toFixed(2) : ""}
                </td>
                <td style={tdStyle}>
                  {annualDividendYield != null
                    ? (annualDividendYield * 100).toFixed(2) + "%"
                    : ""}
                </td>
                <td style={tdStyle}>
                  {expenseRatio != null
                    ? (expenseRatio * 100).toFixed(2) + "%"
                    : ""}
                </td>
                <td style={tdStyle}>
                  {past12MoReturn != null
                    ? (past12MoReturn * 100).toFixed(1) + "%"
                    : ""}
                </td>
                <td style={tdStyle}>{tenYearDisplay}</td>
                <td style={tdStyle}>
                  <input
                    type="number"
                    value={value}
                    onChange={(e) => {
                      const val = parseFloat(e.target.value) || 0;
                      handleChange(i, "value", val);
                    }}
                    style={{ width: "90px" }}
                  />
                </td>
                <td style={tdStyle}>{pctOfPortfolio} %</td>
                <td style={tdStyle}>
                  {rows.length > 1 && (
                    <button onClick={() => handleRemoveRow(i)}>Remove</button>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {rows.length < MAX_TICKERS && (
        <button onClick={handleAddRow} style={{ marginTop: "0.5rem" }}>
          Add Row
        </button>
      )}
    </div>
  );
}

const thStyle = {
  border: "1px solid #ccc",
  padding: "4px 8px",
  background: "#f2f2f2",
  textAlign: "left"
};

const tdStyle = {
  border: "1px solid #ccc",
  padding: "4px 8px"
};
