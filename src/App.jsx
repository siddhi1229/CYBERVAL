import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { TelemetryProvider } from './context/TelemetryContext';
import AppLayout from './components/layout/AppLayout';

import ExecutiveDashboard from './pages/ExecutiveDashboard';
import TechnicalDashboard from './pages/TechnicalDashboard';
import RiskDashboard from './pages/RiskDashboard';
import AttackGraphPage from './pages/AttackGraphPage';
import SimulationPage from './pages/SimulationPage';
import InvestmentPage from './pages/InvestmentPage';
import CompliancePage from './pages/CompliancePage';
import CopilotPage from './pages/CopilotPage';
import ReportsPage from './pages/ReportsPage';

export default function App() {
  return (
    <TelemetryProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<Navigate to="/executive" replace />} />
            <Route path="executive" element={<ExecutiveDashboard />} />
            <Route path="technical" element={<TechnicalDashboard />} />
            <Route path="risk" element={<RiskDashboard />} />
            <Route path="attack-graph" element={<AttackGraphPage />} />
            <Route path="simulation" element={<SimulationPage />} />
            <Route path="investment" element={<InvestmentPage />} />
            <Route path="compliance" element={<CompliancePage />} />
            <Route path="copilot" element={<CopilotPage />} />
            <Route path="reports" element={<ReportsPage />} />
            <Route path="*" element={<Navigate to="/executive" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </TelemetryProvider>
  );
}
