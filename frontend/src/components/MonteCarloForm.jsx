import React, { useState } from "react";

const MonteCarloForm = ({ onSimulate }) => {
  const [initialInvestment, setInitialInvestment] = useState(800000);
  const [years, setYears] = useState(5);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSimulate({
      initial_investment: Number(initialInvestment),
      years: Number(years),
      // Add more fields if needed
    });
  };

  return (
    <form onSubmit={handleSubmit} style={{marginBottom: "1rem"}}>
      <div>
        <label>Initial Investment: </label>
        <input
          type="number"
          value={initialInvestment}
          onChange={(e) => setInitialInvestment(e.target.value)}
        />
      </div>
      <div>
        <label>Years to Simulate: </label>
        <input
          type="number"
          value={years}
          onChange={(e) => setYears(e.target.value)}
        />
      </div>
      <button type="submit">Run Simulation</button>
    </form>
  );
};

export default MonteCarloForm;
