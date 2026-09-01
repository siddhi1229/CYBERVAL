import React, { createContext, useContext, useState, useEffect } from 'react';
import apiClient from '../api/client';
import { formatCurrency as fmtCurrency, formatCostLakhs as fmtCostLakhs, NO_DATA } from '../utils/formatters';

const TelemetryContext = createContext();

export function TelemetryProvider({ children }) {
  const [currency, setCurrency] = useState('INR'); // 'INR' or 'USD'
  const [liveMode, setLiveMode] = useState(true);
  const [lastSync, setLastSync] = useState(new Date());
  const [refreshKey, setRefreshKey] = useState(0);

  // Live enterprise summary metrics fetched from /api/risk/enterprise
  const [enterpriseRisk, setEnterpriseRisk] = useState(null);
  const [loadingEnterprise, setLoadingEnterprise] = useState(false);

  useEffect(() => {
    let isMounted = true;
    async function fetchEnterpriseRisk() {
      try {
        setLoadingEnterprise(true);
        const res = await apiClient.get('/risk/enterprise');
        if (isMounted) {
          setEnterpriseRisk(res.data);
        }
      } catch (err) {
        console.warn('Could not fetch enterprise risk baseline:', err.message);
        if (isMounted) {
          setEnterpriseRisk(null);
        }
      } finally {
        if (isMounted) setLoadingEnterprise(false);
      }
    }
    fetchEnterpriseRisk();
    return () => { isMounted = false; };
  }, [refreshKey]);

  const formatCurrency = (val, showUnit = true) => {
    return fmtCurrency(val, currency, showUnit);
  };

  const formatCostLakhs = (val) => {
    return fmtCostLakhs(val, currency);
  };

  const triggerRefresh = () => {
    setLastSync(new Date());
    setRefreshKey((prev) => prev + 1);
  };

  return (
    <TelemetryContext.Provider
      value={{
        currency,
        setCurrency,
        liveMode,
        setLiveMode,
        lastSync,
        refreshKey,
        triggerRefresh,
        formatCurrency,
        formatCostLakhs,
        enterpriseRisk,
        loadingEnterprise,
        NO_DATA
      }}
    >
      {children}
    </TelemetryContext.Provider>
  );
}

export const useTelemetry = () => useContext(TelemetryContext);
