import React, { useState, useEffect } from 'react';
import {
  FileText,
  Printer,
  ShieldAlert,
  ShieldCheck,
  DollarSign,
  TrendingDown,
  AlertTriangle,
  Server
} from 'lucide-react';
import { useTelemetry } from '../context/TelemetryContext';
import { executiveApi } from '../api/executiveApi';
import { complianceApi } from '../api/complianceApi';
import { investmentApi } from '../api/investmentApi';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Badge from '../components/common/Badge';
import { NO_DATA } from '../utils/formatters';

export default function ReportsPage() {
  const { formatCurrency, refreshKey } = useTelemetry();
  const [execData, setExecData] = useState(null);
  const [complianceData, setComplianceData] = useState([]);
  const [controlsData, setControlsData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadReportData() {
      try {
        setLoading(true);
        const [execRes, compRes, ctrlsRes] = await Promise.allSettled([
          executiveApi.getOverview(),
          complianceApi.getComplianceCoverage(),
          investmentApi.getControls(),
        ]);
        if (execRes.status === 'fulfilled') setExecData(execRes.value);
        if (compRes.status === 'fulfilled') setComplianceData(compRes.value || []);
        if (ctrlsRes.status === 'fulfilled') setControlsData(ctrlsRes.value || []);
      } catch (err) {
        console.error('Failed to aggregate executive report data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadReportData();
  }, [refreshKey]);

  if (loading) return <LoadingSpinner text="Generating live Executive Board Briefing & Compliance Evidence Report..." />;

  const currentDate = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  const totalEalDisplay = execData?.totalExpectedAnnualLoss != null
    ? formatCurrency(execData.totalExpectedAnnualLoss)
    : NO_DATA;

  const totalMapped = complianceData.reduce((acc, c) => acc + (c.mapped_controls || 0), 0);
  const totalControls = complianceData.reduce((acc, c) => acc + (c.total_controls || 0), 0);
  const auditCoveragePct = totalControls > 0 ? ((totalMapped / totalControls) * 100).toFixed(1) : NO_DATA;

  return (
    <div className="space-y-6 max-w-6xl mx-auto print:p-0">
      
      {/* Top Action Bar (hidden in print) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-lg cyber-card border-cv-border bg-white no-print">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-cv-blueLight text-cv-blue border border-blue-200">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-bold text-cv-text font-sans">
              Executive Cyber-Risk & Regulatory Audit Briefing
            </h1>
            <p className="text-xs text-cv-muted font-mono">
              Consolidated Board Document • PostgreSQL Baseline Store
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3 font-mono text-xs">
          <button
            onClick={() => window.print()}
            className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-cv-blue text-white font-bold hover:bg-blue-700 transition-all shadow-sm"
          >
            <Printer className="w-4 h-4" />
            <span>PRINT / EXPORT PDF</span>
          </button>
        </div>
      </div>

      {/* Main Printable Document Container */}
      <div className="p-8 sm:p-10 rounded-xl cyber-card border-cv-border bg-white space-y-8 font-mono text-xs text-cv-text print:bg-white print:text-black print:border-none print:shadow-none">
        
        {/* Document Header */}
        <div className="border-b border-cv-border pb-6 print:border-black flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-lg font-black tracking-widest text-cv-text font-sans print:text-black">
                CYBERVAL
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-cv-blueLight text-cv-blue border border-blue-200 font-bold print:border-black print:text-black print:bg-gray-100">
                BOARD CONFIDENTIAL
              </span>
            </div>
            <h2 className="text-xl font-extrabold text-cv-text font-sans mt-2 tracking-tight print:text-black">
              Executive Cyber Risk Quantification & Regulatory Compliance Audit
            </h2>
            <p className="text-cv-muted text-xs mt-1 print:text-gray-700">
              Generated: {currentDate} • Master Evaluation Baseline
            </p>
          </div>

          <div className="text-right space-y-1">
            <div className="text-[11px] text-cv-muted">CALCULATION VERSION</div>
            <div className="text-sm font-bold text-cv-blue font-sans">{execData?.calculationVersion || 'baseline-1'}</div>
          </div>
        </div>

        {/* Executive Summary Metrics Card */}
        <div className="p-5 rounded-lg bg-cv-bg border border-cv-border space-y-3 print:border-black print:bg-gray-50">
          <span className="font-bold text-xs uppercase text-cv-text tracking-wider block border-b border-cv-border pb-2 print:border-black">
            Executive Summary Key Indicators
          </span>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-1">
            <div>
              <p className="text-cv-muted">Expected Annual Loss</p>
              <p className="text-lg font-black text-cv-danger font-sans">{totalEalDisplay}</p>
            </div>
            <div>
              <p className="text-cv-muted">Evaluated Asset Risks</p>
              <p className="text-lg font-black text-cv-text font-sans">{execData?.riskCount || 0}</p>
            </div>
            <div>
              <p className="text-cv-muted">Regulatory Coverage</p>
              <p className="text-lg font-black text-cv-success font-sans">{auditCoveragePct}%</p>
            </div>
            <div>
              <p className="text-cv-muted">Active Master Controls</p>
              <p className="text-lg font-black text-cv-blue font-sans">{controlsData.length}</p>
            </div>
          </div>
        </div>

        {/* Priority Asset Risks */}
        <div className="space-y-3">
          <h3 className="font-bold text-sm text-cv-text uppercase border-b border-cv-border pb-2 print:border-black">
            Priority Quantified Asset Risks
          </h3>
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="border-b border-cv-border text-cv-muted text-[11px] print:border-black">
                <th className="pb-2">ASSET</th>
                <th className="pb-2">CRITICALITY</th>
                <th className="pb-2">PRIMARY CVE</th>
                <th className="pb-2">FINANCIAL IMPACT</th>
                <th className="pb-2">EXPECTED ANNUAL LOSS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-cv-border print:divide-black">
              {(execData?.topRiskContributors || []).slice(0, 5).map((c) => (
                <tr key={c.id}>
                  <td className="py-2.5 font-bold text-cv-text">{c.assetName}</td>
                  <td className="py-2.5 uppercase">{c.criticality}</td>
                  <td className="py-2.5 text-cv-blue">{c.cve}</td>
                  <td className="py-2.5">{formatCurrency(c.financialExposure)}</td>
                  <td className="py-2.5 font-bold text-cv-danger">{formatCurrency(c.ealContribution)}</td>
                </tr>
              ))}
              {(!execData?.topRiskContributors || execData.topRiskContributors.length === 0) && (
                <tr>
                  <td colSpan="5" className="py-4 text-center text-cv-muted">{NO_DATA}</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Regulatory Framework Compliance Status */}
        <div className="space-y-3">
          <h3 className="font-bold text-sm text-cv-text uppercase border-b border-cv-border pb-2 print:border-black">
            Regulatory Framework Control Mappings
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {complianceData.map((fw) => {
              const pct = fw.total_controls > 0 ? Math.round((fw.mapped_controls / fw.total_controls) * 100) : 0;
              return (
                <div key={fw.framework} className="p-3 bg-cv-bg rounded border border-cv-border print:border-black">
                  <div className="text-[11px] font-bold text-cv-text">{fw.framework}</div>
                  <div className="text-base font-extrabold text-cv-success mt-1">{pct}%</div>
                  <div className="text-[10px] text-cv-muted">{fw.mapped_controls} of {fw.total_controls} controls</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Sign-Off Footer */}
        <div className="pt-8 border-t border-cv-border print:border-black flex justify-between text-cv-muted text-[11px]">
          <div>CYBERVAL Platform Foundation • P6 Frontend Governance</div>
          <div>Page 1 of 1</div>
        </div>

      </div>

    </div>
  );
}
