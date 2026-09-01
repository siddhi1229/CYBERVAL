import React, { createContext, useContext, useState, useEffect } from 'react';

const TelemetryContext = createContext();

export function TelemetryProvider({ children }) {
  const [currency, setCurrency] = useState('INR'); // 'INR' or 'USD'
  const [liveMode, setLiveMode] = useState(true);
  const [lastSync, setLastSync] = useState(new Date());
  const [activeAlertsCount, setActiveAlertsCount] = useState(3);
  const [refreshKey, setRefreshKey] = useState(0);

  // Currency rate constant (1 Cr INR ~ $120K USD approx for display conversion)
  const INR_TO_USD_CR = 0.12; // 1 Cr INR = $0.12M USD

  const formatCurrency = (valInCr, showUnit = true) => {
    if (valInCr === undefined || valInCr === null || isNaN(valInCr)) return '—';
    const num = Number(valInCr);
    
    if (currency === 'INR') {
      return showUnit ? `₹${num.toFixed(1)} Cr` : `₹${num.toFixed(1)}`;
    } else {
      const inMillions = (num * INR_TO_USD_CR).toFixed(2);
      return showUnit ? `$${inMillions}M` : `$${inMillions}`;
    }
  };

  const formatCostLakhs = (valInCr) => {
    if (currency === 'INR') {
      const lakhs = valInCr * 100;
      if (lakhs >= 100) return `₹${(lakhs/100).toFixed(2)} Cr`;
      return `₹${Math.round(lakhs)} Lakhs`;
    } else {
      const inThousands = Math.round(valInCr * INR_TO_USD_CR * 1000);
      return `$${inThousands}K`;
    }
  };

  const triggerRefresh = () => {
    setLastSync(new Date());
    setRefreshKey(prev => prev + 1);
  };

  return (
    <TelemetryContext.Provider
      value={{
        currency,
        setCurrency,
        liveMode,
        setLiveMode,
        lastSync,
        activeAlertsCount,
        refreshKey,
        triggerRefresh,
        formatCurrency,
        formatCostLakhs
      }}
    >
      {children}
    </TelemetryContext.Provider>
  );
}

export const useTelemetry = () => useContext(TelemetryContext);
