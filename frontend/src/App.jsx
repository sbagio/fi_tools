// src/App.jsx

import React, { useState } from "react";
import MonteCarloForm from "./components/MonteCarloForm";
import TickerTable from "./components/TickerTable";
import SimulationChart from "./components/SimulationChart";

function App() {
  // We'll store the simulation results
  const [results, setResults] = useState(null);

  // We can also store the rows from TickerTable if we want to pass them
  // into the simulation. For example, we might convert the "value" fields
  // to weights for the simulation.
  const [tableRows, setTableRows] = useState([]);

  // Called when user clicks "Run Simulation" in MonteCarloForm
  const handleSimulate = async (formData) => {
    try {
      // Convert tableRows => tickers & weights:
      // 1. Filter out rows with empty ticker or zero value
      const validRows = tableRows.filter((r) => r.ticker && r.value > 0);
      if (validRows.length === 0) {
        alert("No valid tickers in the table. Please add at least one ticker with a positive value.");
        return;
      }

      // 2. Sum total
      const totalValue = validRows.reduce((sum, r) => sum + r.value, 0);
      // 3. Build arrays for simulation
      const tickers = validRows.map((r) => r.ticker);
      const weights = validRows.map((r) => r.value / totalValue);

      // Merge with any formData
      const payload = {
        ...formData,
        tickers,
        weights
      };

      // POST to /simulate
      const res = await fetch("http://localhost:5000/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (data.error) {
        throw new Error(data.error);
      }
      setResults(data);
    } catch (error) {
      console.error("Simulation error:", error);
      alert(`Error running simulation: ${error.message}`);
    }
  };

  // Called by TickerTable whenever rows change
  const handleTableChange = (updatedRows) => {
    setTableRows(updatedRows);
  };

  return (
    <div style={{ padding: "1rem" }}>
      <h1>Monte Carlo Simulation App</h1>

      {/* 1) The dynamic ticker table */}
      <TickerTable onTableChange={handleTableChange} />

      {/* 2) The form for simulation inputs (e.g. years, number of sims, etc.) */}
      <MonteCarloForm onSimulate={handleSimulate} />

      {/* 3) Display results + histogram */}
      {results && (
        <div style={{ marginTop: "1rem" }}>
          <h2>Results</h2>
          <p>25th percentile: ${results.pct_25?.toFixed(2)}</p>
          <p>Median (50th): ${results.pct_50?.toFixed(2)}</p>
          <p>75th percentile: ${results.pct_75?.toFixed(2)}</p>
          <p>Mean: ${results.mean?.toFixed(2)}</p>

          {results.all_final_values && (
            <SimulationChart finalValues={results.all_final_values} />
          )}
        </div>
      )}
    </div>
  );
}

export default App;
