/**
 * CYBERVAL Centralized Formatters & Data Integrity Utilities
 */

export const NO_DATA = "No data available";

/**
 * Format currency in INR (Crores / Lakhs) or USD (Millions / Thousands).
 * Handles raw currency units (e.g. 42,750,000 INR) as well as Cr scalars (e.g. 4.28).
 */
export function formatCurrency(value, currency = 'INR', showUnit = true) {
  if (value === undefined || value === null || isNaN(Number(value))) {
    return NO_DATA;
  }

  let num = Number(value);

  // If number is large (> 1,000,000), it is in raw INR from PostgreSQL
  if (Math.abs(num) >= 1000000) {
    num = num / 10000000; // Convert to Crores
  }

  const INR_TO_USD_CR = 0.12; // 1 Cr INR ~ $0.12M USD

  if (currency === 'INR') {
    const formatted = num.toFixed(2);
    return showUnit ? `₹${formatted} Cr` : `₹${formatted}`;
  } else {
    const inMillions = (num * INR_TO_USD_CR).toFixed(2);
    return showUnit ? `$${inMillions}M` : `$${inMillions}`;
  }
}

/**
 * Format cost in Lakhs or Crores
 */
export function formatCostLakhs(value, currency = 'INR') {
  if (value === undefined || value === null || isNaN(Number(value))) {
    return NO_DATA;
  }

  let num = Number(value);
  if (Math.abs(num) >= 1000000) {
    num = num / 10000000; // to Crores
  }

  const INR_TO_USD_CR = 0.12;

  if (currency === 'INR') {
    const lakhs = num * 100;
    if (lakhs >= 100) return `₹${(lakhs / 100).toFixed(2)} Cr`;
    return `₹${Math.round(lakhs)} Lakhs`;
  } else {
    const inThousands = Math.round(num * INR_TO_USD_CR * 1000);
    return `$${inThousands}K`;
  }
}

/**
 * Safely format percentage
 */
export function formatPercent(value, decimals = 1) {
  if (value === undefined || value === null || isNaN(Number(value))) {
    return NO_DATA;
  }
  return `${Number(value).toFixed(decimals)}%`;
}

/**
 * Safely format risk scores (0-100)
 */
export function formatRiskScore(score) {
  if (score === undefined || score === null || isNaN(Number(score))) {
    return NO_DATA;
  }
  return `${Number(score).toFixed(1)} / 100`;
}
