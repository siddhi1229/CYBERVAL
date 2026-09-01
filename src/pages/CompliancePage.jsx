import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  FileCheck,
  Filter,
  ExternalLink,
  Layers,
  Search,
  BookOpen,
  DollarSign,
  Server
} from 'lucide-react';
import MetricCard from '../components/common/MetricCard';
import Badge from '../components/common/Badge';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Modal from '../components/common/Modal';
import { useTelemetry } from '../context/TelemetryContext';
import { complianceApi } from '../api/complianceApi';

export default function CompliancePage() {
  const { formatCurrency, refreshKey } = useTelemetry();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [selectedFramework, setSelectedFramework] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedControl, setSelectedControl] = useState(null);

  useEffect(() => {
    async function loadCompliance() {
      try {
        setLoading(true);
        const result = await complianceApi.getMasterMapping();
        setData(result);
        setError(null);
      } catch (err) {
        console.error('Error loading compliance master mapping:', err);
        setError('Failed to fetch compliance mapping.');
      } finally {
        setLoading(false);
      }
    }
    loadCompliance();
  }, [refreshKey]);

  if (loading) return <LoadingSpinner text="Harmonizing Master Controls Across NIST, ISO, CIS, RBI, SEBI..." />;
  if (error || !data) {
    return (
      <div className="p-8 text-center text-cv-danger border border-red-200 rounded-lg bg-red-50 font-mono">
        <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-cv-danger" />
        <p>{error || 'Compliance data unavailable.'}</p>
      </div>
    );
  }

  const filteredControls = data.masterControls.filter((ctrl) => {
    const matchesSearch =
      ctrl.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ctrl.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ctrl.domain.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ctrl.evidenceStatus.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  return (
    <div className="space-y-6">
      
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-lg cyber-card border-cv-border">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cv-successBg text-cv-success border border-green-200">
              UNIFIED MASTER CONTROL ENGINE
            </span>
            <span className="text-xs font-mono text-cv-muted">
              Single Master Control → NIST • ISO 27001 • CIS • RBI CSF • SEBI CSCRF
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-cv-text mt-1 tracking-tight">
            Master Compliance & Regulatory Framework Mapping
          </h1>
          <p className="text-xs sm:text-sm text-cv-muted mt-0.5">
            Cross-regulatory compliance harmonized under unified Master Controls with automated telemetry evidence.
          </p>
        </div>

        <div className="flex items-center space-x-2 font-mono text-xs">
          <div className="px-3 py-2 rounded-lg bg-cv-bg border border-cv-border text-cv-text">
            AUDIT READINESS: <strong className="text-cv-success">{data.overallComplianceScore}%</strong>
          </div>
        </div>
      </div>

      {/* 5 Regulatory Framework Compliance Scorecards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 font-mono">
        {data.frameworkStats.map((fw, idx) => (
          <div
            key={idx}
            onClick={() => {
              const code = fw.name.includes('RBI') ? 'RBI' : fw.name.includes('SEBI') ? 'SEBI' : fw.name.includes('NIST') ? 'NIST' : fw.name.includes('ISO') ? 'ISO' : 'CIS';
              setSelectedFramework(selectedFramework === code ? 'ALL' : code);
            }}
            className={`p-3.5 rounded-lg border transition-all cursor-pointer ${
              selectedFramework !== 'ALL' && !fw.name.toUpperCase().includes(selectedFramework)
                ? 'bg-cv-bg border-cv-border opacity-50'
                : 'bg-white border-cv-border hover:border-cv-blue hover:shadow-card-md'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-cv-muted font-bold uppercase truncate">{fw.name.split(' ')[0]}</span>
              <span className="text-xs font-bold text-cv-success">{fw.score}%</span>
            </div>
            <div className="text-sm font-bold text-cv-text font-sans mt-1 truncate">
              {fw.name}
            </div>
            <div className="w-full bg-cv-bg rounded-full h-1.5 overflow-hidden mt-2 border border-cv-border">
              <div className="bg-cv-success h-full" style={{ width: `${fw.score}%` }} />
            </div>
            <div className="flex justify-between text-[10px] text-cv-muted mt-1.5">
              <span>{fw.compliant} Compliant</span>
              <span className="text-cv-danger">{fw.nonCompliant} Gaps</span>
            </div>
          </div>
        ))}
      </div>

      {/* Master Control Mapping Table Section */}
      <div className="cyber-card rounded-lg border-cv-border overflow-hidden space-y-3 p-5">
        
        {/* Table Filter & Framework View Switcher */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-cv-border pb-3">
          <div className="flex flex-wrap items-center gap-1.5 font-mono text-xs">
            <span className="text-cv-muted mr-2 flex items-center">
              <Filter className="w-3.5 h-3.5 mr-1" /> View:
            </span>
            {['ALL', 'RBI', 'SEBI', 'NIST', 'ISO', 'CIS'].map((mode) => (
              <button
                key={mode}
                onClick={() => setSelectedFramework(mode)}
                className={`px-3 py-1 rounded-lg font-bold transition-colors ${
                  selectedFramework === mode
                    ? 'bg-cv-blue text-white shadow-sm'
                    : 'bg-cv-bg text-cv-muted hover:text-cv-text border border-cv-border'
                }`}
              >
                {mode === 'ALL' ? 'Unified Master (All 5)' : mode}
              </button>
            ))}
          </div>

          <div className="flex items-center space-x-2 font-mono text-xs">
            <Search className="w-4 h-4 text-cv-blue" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search master control, title, or evidence..."
              className="px-3 py-1.5 bg-cv-bg border border-cv-border rounded-lg text-xs text-cv-text focus:outline-none focus:border-cv-blue w-64"
            />
          </div>
        </div>

        {/* Master Controls Accordion / Table */}
        <div className="space-y-3 font-mono text-xs">
          {filteredControls.map((ctrl) => (
            <div
              key={ctrl.id}
              className="p-4 rounded-lg bg-cv-bg border border-cv-border hover:border-slate-300 transition-all space-y-3"
            >
              {/* Header Row */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-cv-border pb-2">
                <div className="flex items-center space-x-3">
                  <span className="px-2.5 py-1 rounded bg-cv-blueLight text-cv-blue border border-blue-200 font-bold text-xs">
                    {ctrl.code}
                  </span>
                  <div>
                    <h3 className="font-bold text-cv-text font-sans text-sm">{ctrl.title}</h3>
                    <span className="text-[10px] text-cv-muted">{ctrl.domain}</span>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <span className="text-cv-muted text-[10px] block">FINANCIAL RISK IMPACT</span>
                    <span className="font-bold text-cv-danger">{ctrl.financialRiskContribution}</span>
                  </div>

                  <div className="text-right">
                    <span className="text-cv-muted text-[10px] block">AFFECTED ASSETS</span>
                    <span className="font-bold text-cv-text">{ctrl.affectedAssetsCount} Hosts</span>
                  </div>

                  <Badge
                    variant={ctrl.status === 'COMPLIANT' ? 'compliant' : ctrl.status === 'PARTIAL' ? 'partial' : 'noncompliant'}
                    size="sm"
                  >
                    {ctrl.status === 'COMPLIANT' ? 'COMPLIANT' : ctrl.status === 'PARTIAL' ? 'PARTIALLY COMPLIANT' : 'NON-COMPLIANT'}
                  </Badge>
                </div>
              </div>

              {/* Framework Cross-Mapping Chips */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2 text-[11px]">
                
                <div className={`p-2 rounded border ${selectedFramework === 'NIST' || selectedFramework === 'ALL' ? 'border-blue-200 bg-cv-blueLight' : 'border-cv-border bg-white'}`}>
                  <span className="text-[10px] text-cv-blue font-bold block">NIST CSF 2.0</span>
                  <span className="text-cv-muted">{ctrl.frameworks.nist}</span>
                </div>

                <div className={`p-2 rounded border ${selectedFramework === 'ISO' || selectedFramework === 'ALL' ? 'border-blue-200 bg-cv-blueLight' : 'border-cv-border bg-white'}`}>
                  <span className="text-[10px] text-cv-blue font-bold block">ISO/IEC 27001</span>
                  <span className="text-cv-muted">{ctrl.frameworks.iso}</span>
                </div>

                <div className={`p-2 rounded border ${selectedFramework === 'CIS' || selectedFramework === 'ALL' ? 'border-purple-200 bg-purple-50' : 'border-cv-border bg-white'}`}>
                  <span className="text-[10px] text-purple-700 font-bold block">CIS Controls v8</span>
                  <span className="text-cv-muted">{ctrl.frameworks.cis}</span>
                </div>

                <div className={`p-2 rounded border ${selectedFramework === 'RBI' || selectedFramework === 'ALL' ? 'border-amber-200 bg-cv-warningBg' : 'border-cv-border bg-white'}`}>
                  <span className="text-[10px] text-cv-warning font-bold block">RBI CSF (Annexure I)</span>
                  <span className="text-cv-muted">{ctrl.frameworks.rbi}</span>
                </div>

                <div className={`p-2 rounded border ${selectedFramework === 'SEBI' || selectedFramework === 'ALL' ? 'border-green-200 bg-cv-successBg' : 'border-cv-border bg-white'}`}>
                  <span className="text-[10px] text-cv-success font-bold block">SEBI CSCRF</span>
                  <span className="text-cv-muted">{ctrl.frameworks.sebi}</span>
                </div>

              </div>

              {/* Evidence & Telemetry Link */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-2.5 rounded bg-white border border-cv-border text-[11px]">
                <div className="flex items-center space-x-2 text-cv-muted">
                  <FileCheck className="w-4 h-4 text-cv-success flex-shrink-0" />
                  <span><strong className="text-cv-text">Audit Evidence:</strong> {ctrl.evidenceStatus}</span>
                </div>
                <div className="flex items-center space-x-3 text-cv-muted text-[10px]">
                  <span>Last Audited: {ctrl.lastAudited}</span>
                  <button
                    onClick={() => setSelectedControl(ctrl)}
                    className="text-cv-blue hover:text-blue-700 flex items-center space-x-1 font-bold"
                  >
                    <span>Inspect Evidence</span>
                    <ExternalLink className="w-3 h-3" />
                  </button>
                </div>
              </div>

            </div>
          ))}
        </div>
      </div>

      {/* Audit Evidence Modal */}
      {selectedControl && (
        <Modal
          isOpen={!!selectedControl}
          onClose={() => setSelectedControl(null)}
          title={`Master Control Evidence: ${selectedControl.code} - ${selectedControl.title}`}
          size="md"
        >
          <div className="space-y-4 font-mono text-xs">
            <div className="p-3 rounded-lg bg-cv-bg border border-cv-border space-y-2">
              <div className="flex justify-between">
                <span className="text-cv-muted">Implementation Status:</span>
                <Badge variant={selectedControl.status === 'COMPLIANT' ? 'compliant' : 'partial'}>
                  {selectedControl.status}
                </Badge>
              </div>
              <div className="flex justify-between">
                <span className="text-cv-muted">Telemetric Proof Link:</span>
                <span className="text-cv-blue">{selectedControl.evidenceUrl}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-cv-muted">Last Verified Timestamp:</span>
                <span className="text-cv-text">{selectedControl.lastAudited}</span>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-cv-bg border border-cv-border space-y-2">
              <h4 className="font-bold text-cv-text uppercase">Live Telemetry Proof:</h4>
              <p className="text-cv-muted text-xs">
                {selectedControl.evidenceStatus}
              </p>
            </div>

            <div className="flex justify-end">
              <button
                onClick={() => setSelectedControl(null)}
                className="px-4 py-2 bg-cv-bg hover:bg-cv-blueLight rounded-lg text-cv-text border border-cv-border font-bold transition-colors"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </Modal>
      )}

    </div>
  );
}
