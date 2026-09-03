import React, { useState } from 'react';
import {
  ShieldAlert,
  Activity,
  RefreshCw,
  Search,
  Bell,
  Sliders,
  DollarSign,
  Download,
  Terminal,
  ExternalLink,
  CheckCircle2,
  AlertOctagon,
  User,
  Shield
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
    activeAlertsCount,
    formatCurrency
  } = useTelemetry();

  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isReportOpen, setIsReportOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const searchResults = [
    { label: 'Core Banking Oracle DB (AST-001)', category: 'Crown Jewel Asset', route: '/technical' },
    { label: 'Citrix Bleed (CVE-2023-4966)', category: 'Critical Vulnerability', route: '/technical' },
    { label: 'Hardware MFA Enforcement (MC-04)', category: 'Master Control', route: '/compliance' },
    { label: 'Perimeter Killchain to Swift Gateway', category: 'Attack Path', route: '/attack-graph' },
    { label: 'What-If Simulation for Micro-segmentation', category: 'Simulation', route: '/simulation' }
  ].filter(item => item.label.toLowerCase().includes(searchQuery.toLowerCase()) || item.category.toLowerCase().includes(searchQuery.toLowerCase()));

  return (
    <>
      <header className="sticky top-0 z-40 w-full border-b border-cv-border bg-white/95 backdrop-blur-md">
        <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
          
          {/* Brand Logo & Telemetry Indicator */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2.5">
              <div className="relative flex items-center justify-center w-9 h-9 rounded-lg bg-gradient-to-tr from-cv-blue to-blue-600 border border-blue-700 shadow-sm">
                <ShieldAlert className="w-5 h-5 text-white" />
                <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-cv-success ring-2 ring-white" />
              </div>
              <div>
                <span className="text-lg font-extrabold tracking-wider text-cv-text font-sans">
                  CYBERVAL
                </span>
                <span className="ml-1.5 text-[10px] font-mono px-1.5 py-0.5 rounded bg-cv-blueLight text-cv-blue border border-blue-200 font-semibold">
                  ENTERPRISE
                </span>
              </div>
            </div>

            {/* Live Ticker Bar */}
            <div className="hidden lg:flex items-center space-x-3 pl-4 border-l border-cv-border text-xs font-mono text-cv-muted">
              <div className="flex items-center space-x-1.5 px-2 py-1 rounded bg-cv-bg border border-cv-border">
                <span className="text-cv-muted">RISK SCORE:</span>
                <strong className="text-cv-danger">74</strong>
                <span className="text-[10px] text-cv-success font-bold">LIVE</span>
              </div>
              
              <div className="flex items-center space-x-1.5 px-2 py-1 rounded bg-cv-bg border border-cv-border">
                <span className="text-cv-muted">YEARLY LOSS:</span>
                <strong className="text-cv-text">{formatCurrency(54.7)}</strong>
              </div>

              <div className="flex items-center space-x-1.5 px-2 py-1 rounded bg-cv-bg border border-cv-border">
                <span className="text-cv-muted">WORST CASE:</span>
                <strong className="text-cv-warning">{formatCurrency(94.1)}</strong>
              </div>

              <div className="flex items-center space-x-1.5 text-[11px] text-cv-success pl-1">
                <span className="w-2 h-2 rounded-full bg-cv-success animate-pulse" />
                <span className="font-semibold">CONNECTED</span>
              </div>
            </div>
          </div>

          {/* Center Search / Command Trigger */}
          <div className="flex-1 max-w-md mx-4 hidden md:block">
            <button
              onClick={() => setIsSearchOpen(true)}
              className="w-full flex items-center justify-between px-3.5 py-1.5 rounded-lg bg-cv-bg border border-cv-border hover:border-cv-blue text-cv-muted text-xs font-mono transition-all shadow-xs"
            >
              <div className="flex items-center space-x-2">
                <Search className="w-4 h-4 text-cv-blue" />
                <span>Search assets, risks, vulnerabilities...</span>
              </div>
              <kbd className="px-1.5 py-0.5 text-[10px] bg-white border border-cv-border rounded text-cv-muted font-sans font-medium">
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
              title="Refresh live telemetry stream"
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

            {/* SecOps User Profile Avatar (Clean, no P6) */}
            <div className="flex items-center space-x-2 pl-2 border-l border-cv-border">
              <div 
                className="w-8 h-8 rounded-lg bg-gradient-to-tr from-slate-800 to-slate-700 border border-slate-600/50 flex items-center justify-center text-white shadow-xs cursor-pointer hover:border-cv-blue transition-all"
                title="SecOps Risk Lead (Logged in)"
              >
                <User className="w-4 h-4 text-slate-200" />
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
              placeholder="Search by CVE, asset IP, business service, killchain, or control ID..."
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

      {/* Executive Briefing Report Modal */}
      <Modal
        isOpen={isReportOpen}
        onClose={() => setIsReportOpen(false)}
        title="CYBERVAL Executive Board Cyber-Risk Briefing (Q1 2026)"
        size="lg"
      >
        <div className="space-y-4 font-mono text-xs">
          <div className="p-4 rounded-lg bg-cv-bg border border-cv-border space-y-2">
            <div className="flex items-center justify-between border-b border-cv-border pb-2">
              <span className="font-bold text-sm text-cv-text font-sans">CONFIDENTIAL BOARD CYBER RISK SUMMARY</span>
              <span className="text-cv-success font-semibold">STATUS: AUDIT READY</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
              <div>
                <p className="text-cv-muted">Enterprise Risk</p>
                <p className="text-lg font-bold text-cv-danger font-sans">71 / 100</p>
              </div>
              <div>
                <p className="text-cv-muted">Expected Annual Loss</p>
                <p className="text-lg font-bold text-cv-text font-sans">{formatCurrency(18.4)}</p>
              </div>
              <div>
                <p className="text-cv-muted">P95 VaR Exposure</p>
                <p className="text-lg font-bold text-cv-warning font-sans">{formatCurrency(31.7)}</p>
              </div>
              <div>
                <p className="text-cv-muted">Actionable Reduction</p>
                <p className="text-lg font-bold text-cv-success font-sans">{formatCurrency(6.5)}</p>
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="font-bold text-cv-text uppercase">Key Executive Findings & Risk Drivers:</h4>
            <ul className="list-disc list-inside space-y-1 text-cv-muted">
              <li><strong className="text-cv-text">Ransomware Threat Vector:</strong> Active exploit path CVE-2023-4966 targeting Core Banking Oracle RAC DB poses 39.1% of total enterprise financial risk ({formatCurrency(7.2)} EAL).</li>
              <li><strong className="text-cv-text">Regulatory Mandate Compliance:</strong> Overall compliance is 76.0% (RBI CSF) and 79.6% (SEBI CSCRF). 3 critical patch SLAs are currently overdue in Treasury.</li>
              <li><strong className="text-cv-text">Recommended Capital Allocation:</strong> Funding ₹1.30 Cr across Hardware MFA (MC-04) and Core Banking Micro-segmentation (MC-11) reduces enterprise EAL by {formatCurrency(6.5)} with a 400% ROSI.</li>
            </ul>
          </div>

          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-cv-border">
            <button
              onClick={() => {
                window.print();
                setIsReportOpen(false);
              }}
              className="px-4 py-2 rounded-lg bg-cv-blue text-white font-bold hover:bg-blue-700 transition-colors flex items-center space-x-2"
            >
              <Download className="w-4 h-4" />
              <span>Print / Export PDF Briefing</span>
            </button>
          </div>
        </div>
      </Modal>
    </>
  );
}
