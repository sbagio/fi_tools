import React, { useMemo } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";

/**
 * SimulationChart
 * 
 * Displays a histogram of final portfolio values from the Monte Carlo simulation.
 * 
 * Props:
 *   finalValues: array of final portfolio values (numbers).
 */
function SimulationChart({ finalValues }) {
  // We'll bin the data into a certain number of buckets (e.g., 30).
  // This is done inside a useMemo so it doesn't recalc on every render.
  const chartData = useMemo(() => {
    if (!finalValues || finalValues.length === 0) {
      return [];
    }

    // Sort the final values in ascending order
    const sorted = [...finalValues].sort((a, b) => a - b);

    // Number of bins
    const binCount = 30;

    // Minimum and maximum values
    const minVal = sorted[0];
    const maxVal = sorted[sorted.length - 1];

    // Edge case: if minVal == maxVal, all results are identical
    if (minVal === maxVal) {
      return [{ name: minVal.toFixed(2), count: finalValues.length }];
    }

    // The range of values
    const range = maxVal - minVal;
    // Each bin covers this range
    const binSize = range / binCount;

    // Initialize bins to zero
    const bins = Array(binCount).fill(0);

    // Place each final value into the appropriate bin
    sorted.forEach((val) => {
      const binIndex = Math.floor((val - minVal) / binSize);
      // Ensure the index doesn't exceed binCount-1 due to floating-point rounding
      const safeIndex = Math.min(binCount - 1, binIndex);
      bins[safeIndex]++;
    });

    // Convert bin counts to Recharts-friendly objects
    return bins.map((count, i) => {
      const binStart = minVal + i * binSize;
      const binEnd = binStart + binSize;
      return {
        name: `${binStart.toFixed(0)} - ${binEnd.toFixed(0)}`,
        count,
      };
    });
  }, [finalValues]);

  return (
    <div style={{ marginTop: "20px" }}>
      <h3>Distribution of Final Portfolio Values</h3>
      {chartData.length > 0 ? (
        <BarChart width={600} height={300} data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" angle={-45} textAnchor="end" height={60} />
          <YAxis />
          <Tooltip />
          <Bar dataKey="count" fill="#8884d8" />
        </BarChart>
      ) : (
        <p>No final values to display.</p>
      )}
    </div>
  );
}

export default SimulationChart;
