import React, { useState } from 'react';
import {
  ShieldAlert,
  Activity,
  RefreshCw,
  Search,
  Sliders,
  DollarSign,
  Download,
  Terminal,
  ExternalLink,
  CheckCircle2,
  AlertOctagon
} from 'lucide-react';
import { useTelemetry } from '../../context/TelemetryContext';
import Modal from '../common/Modal';

export default function Navbar() {
  const {
    currency,
    setCurrency,
    liveMode,
    setLiveMode,
    lastSync,
    triggerRefresh,
    formatCurrency,
    enterpriseRisk,
    NO_DATA
  } = useTelemetry();

  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isReportOpen, setIsReportOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const searchResults = [
    { label: 'Payment Gateway (PAYMENT-API-01)', category: 'Internet Exposed Asset', route: '/technical' },
    { label: 'Internet Gateway', category: 'Perimeter Asset', route: '/technical' },
    { label: 'Customer Database', category: 'Crown Jewel Asset', route: '/technical' },
    { label: 'Core Banking Server', category: 'Crown Jewel Asset', route: '/technical' },
    { label: 'FortiOS RCE (CVE-2024-21762)', category: 'Critical Vulnerability', route: '/technical' },
    { label: 'XZ Utils Backdoor (CVE-2024-3094)', category: 'Supply Chain CVE', route: '/technical' },
    { label: 'Multi-factor Authentication', category: 'Master Control', route: '/compliance' },
    { label: 'Network Segmentation', category: 'Master Control', route: '/compliance' },
    { label: 'Discovered Attack Paths', category: 'Attack Graph', route: '/attack-graph' },
    { label: 'Investment Portfolio Optimization', category: 'Investment', route: '/investment' },
  ].filter(item => item.label.toLowerCase().includes(searchQuery.toLowerCase()) || item.category.toLowerCase().includes(searchQuery.toLowerCase()));

  const totalEalDisplay = enterpriseRisk?.total_expected_annual_loss != null
    ? formatCurrency(enterpriseRisk.total_expected_annual_loss)
    : NO_DATA;

  const evaluatedRisksDisplay = enterpriseRisk?.risk_count != null
    ? `${enterpriseRisk.risk_count} Assets Evaluated`
    : NO_DATA;

  return (
    <>
      <header className="sticky top-0 z-40 w-full border-b border-cv-border bg-white/95 backdrop-blur-md">
        <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
          
          {/* Brand Logo & Telemetry Indicator */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2.5">
              <div className="relative flex items-center justify-center w-9 h-9 rounded-lg bg-cv-blue border border-blue-700">
                <ShieldAlert className="w-5 h-5 text-white" />
                <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-cv-success ring-2 ring-white" />
              </div>
              <div>
                <span className="text-lg font-extrabold tracking-wider text-cv-text font-sans">
                  CYBERVAL
                </span>
                <span className="ml-1.5 text-[10px] font-mono px-1.5 py-0.5 rounded bg-cv-blueLight text-cv-blue border border-blue-200 font-semibold">
                  ENTERPRISE v1.0
                </span>
              </div>
            </div>

            {/* Live Ticker Bar */}
            <div className="hidden lg:flex items-center space-x-3 pl-4 border-l border-cv-border text-xs font-mono text-cv-muted">
              <div className="flex items-center space-x-1.5 px-2 py-1 rounded bg-cv-bg border border-cv-border">
                <span className="text-cv-muted">TOTAL EAL:</span>
                <strong className="text-cv-danger">{totalEalDisplay}</strong>
              </div>
              
              <div className="flex items-center space-x-1.5 px-2 py-1 rounded bg-cv-bg border border-cv-border">
                <span className="text-cv-muted">RISK COVERAGE:</span>
                <strong className="text-cv-text">{evaluatedRisksDisplay}</strong>
              </div>

              <div className="flex items-center space-x-1.5 text-[11px] text-cv-success pl-1">
                <span className="w-2 h-2 rounded-full bg-cv-success animate-pulse" />
                <span>LIVE API</span>
              </div>
            </div>
          </div>

          {/* Center Search / Command Trigger */}
          <div className="flex-1 max-w-md mx-4 hidden md:block">
            <button
              onClick={() => setIsSearchOpen(true)}
              className="w-full flex items-center justify-between px-3.5 py-1.5 rounded-lg bg-cv-bg border border-cv-border hover:border-cv-blue text-cv-muted text-xs font-mono transition-all"
            >
              <div className="flex items-center space-x-2">
                <Search className="w-4 h-4 text-cv-blue" />
                <span>Search assets, risks, vulnerabilities...</span>
              </div>
              <kbd className="px-1.5 py-0.5 text-[10px] bg-white border border-cv-border rounded text-cv-muted">
                ⌘K
              </kbd>
            </button>
          </div>

          {/* Right Action Controls */}
          <div className="flex items-center space-x-3">
            {/* Currency Unit Switcher */}
            <div className="flex items-center bg-cv-bg border border-cv-border rounded-lg p-0.5 font-mono text-xs">
              <button
                onClick={() => setCurrency('INR')}
                className={`px-2.5 py-1 rounded transition-all font-bold ${
                  currency === 'INR'
                    ? 'bg-cv-blue text-white shadow-sm'
                    : 'text-cv-muted hover:text-cv-text'
                }`}
                title="Display metrics in Indian Rupees (₹ Cr)"
              >
                ₹ INR
              </button>
              <button
                onClick={() => setCurrency('USD')}
                className={`px-2.5 py-1 rounded transition-all font-bold ${
                  currency === 'USD'
                    ? 'bg-cv-blue text-white shadow-sm'
                    : 'text-cv-muted hover:text-cv-text'
                }`}
                title="Display metrics in US Dollars ($ Millions)"
              >
                $ USD
              </button>
            </div>

            {/* Refresh Telemetry */}
            <button
              onClick={triggerRefresh}
              className="p-2 rounded-lg bg-cv-bg border border-cv-border hover:border-cv-blue text-cv-muted hover:text-cv-blue transition-all"
              title="Refresh live telemetry from backend"
            >
              <RefreshCw className="w-4 h-4" />
            </button>

            {/* Executive Report Download / View Button */}
            <a
              href="/reports"
              className="hidden sm:flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-cv-blue text-white hover:bg-blue-700 font-mono text-xs font-semibold transition-all shadow-sm"
            >
              <Download className="w-3.5 h-3.5" />
              <span>EXECUTIVE REPORT</span>
            </a>

            {/* User / Org Avatar */}
            <div className="flex items-center space-x-2 pl-2 border-l border-cv-border">
              <div className="w-8 h-8 rounded-lg bg-cv-blue flex items-center justify-center font-mono font-bold text-xs text-white shadow-sm">
                P6
              </div>
            </div>
          </div>

        </div>
      </header>

      {/* Global Search Modal */}
      <Modal
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        title="Enterprise Cyber-Risk Intelligence Search"
        size="md"
      >
        <div className="space-y-4">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-3 text-cv-blue" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by asset name, CVE, technique, or control..."
              className="w-full pl-9 pr-4 py-2 bg-cv-bg border border-cv-border rounded-lg text-sm font-mono text-cv-text focus:outline-none focus:border-cv-blue"
              autoFocus
            />
          </div>

          <div className="space-y-1 max-h-64 overflow-y-auto">
            {searchResults.map((res, idx) => (
              <a
                key={idx}
                href={res.route}
                onClick={() => setIsSearchOpen(false)}
                className="flex items-center justify-between p-2.5 rounded-lg hover:bg-cv-bg border border-transparent hover:border-cv-border transition-all font-mono text-xs"
              >
                <span className="text-cv-text font-semibold">{res.label}</span>
                <span className="text-cv-blue text-[10px] px-2 py-0.5 rounded bg-cv-blueLight border border-blue-200">
                  {res.category}
                </span>
              </a>
            ))}
            {searchResults.length === 0 && (
              <div className="text-center py-6 text-cv-muted font-mono text-xs">
                No matching telemetry assets found for "{searchQuery}".
              </div>
            )}
          </div>
        </div>
      </Modal>
    </>
  );
}
