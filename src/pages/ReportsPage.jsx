import React, { useState, useEffect, useRef } from 'react';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import {
  FileText,
  Download,
  Printer,
  Loader2,
  ShieldAlert,
  ShieldCheck,
  DollarSign,
  TrendingDown,
  AlertTriangle,
  Award,
  Layers,
  ArrowRight,
  ExternalLink,
  Calendar,
  CheckCircle2
} from 'lucide-react';
import { useTelemetry } from '../context/TelemetryContext';
import { executiveApi } from '../api/executiveApi';
import { complianceApi } from '../api/complianceApi';
import { investmentApi } from '../api/investmentApi';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Badge from '../components/common/Badge';

export default function ReportsPage() {
  const { formatCurrency, refreshKey, currency } = useTelemetry();
  const [execData, setExecData] = useState(null);
  const [complianceData, setComplianceData] = useState(null);
  const [investmentData, setInvestmentData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [exportingPdf, setExportingPdf] = useState(false);
  const reportRef = useRef(null);

  useEffect(() => {
    async function loadReportData() {
      try {
        setLoading(true);
        const [execRes, compRes, invRes] = await Promise.all([
          executiveApi.getOverview(),
          complianceApi.getMasterMapping(),
          investmentApi.getOverview()
        ]);
        setExecData(execRes);
        setComplianceData(compRes);
        setInvestmentData(invRes);
      } catch (err) {
        console.error('Failed to aggregate executive report data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadReportData();
  }, [refreshKey]);

  const handleExportPdf = async () => {
    if (!reportRef.current || exportingPdf) return;
    try {
      setExportingPdf(true);
      const element = reportRef.current;

      // High-resolution canvas rendering
      const canvas = await html2canvas(element, {
        scale: 2,
        useCORS: true,
        logging: false,
        backgroundColor: '#ffffff',
        windowWidth: element.scrollWidth,
      });

      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4',
      });

      const imgWidth = 210; // A4 width in mm
      const pageHeight = 297; // A4 height in mm
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      let heightLeft = imgHeight;
      let position = 0;

      // Add first page
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight, undefined, 'FAST');
      heightLeft -= pageHeight;

      // Add subsequent pages if the report height exceeds one A4 page
      while (heightLeft > 0) {
        position = heightLeft - imgHeight;
        pdf.addPage();
        pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight, undefined, 'FAST');
        heightLeft -= pageHeight;
      }

      const dateStr = new Date().toISOString().split('T')[0];
      pdf.save(`CYBERVAL_Executive_Risk_Report_${dateStr}.pdf`);
    } catch (err) {
      console.error('Failed to export PDF:', err);
    } finally {
      setExportingPdf(false);
    }
  };

  if (loading) return <LoadingSpinner text="Generating Executive Board Briefing & Compliance Evidence Report..." />;

  const currentDate = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  return (
    <div className="space-y-6 max-w-6xl mx-auto print:p-0">
      
      {/* Top Action Bar (hidden in print) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-lg cyber-card border-cv-border bg-white no-print">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-cv-blueLight text-cv-blue border border-blue-200">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-bold text-cv-text font-sans">Executive Cyber-Risk & Regulatory Audit Briefing</h1>
            <p className="text-xs text-cv-muted font-mono">Consolidated Q1 2026 Board Document • FAIR Quantitative Model</p>
          </div>
        </div>

        {/* Separated Action Controls: Print & Export as PDF */}
        <div className="flex items-center space-x-2.5 font-mono text-xs">
          {/* 1. Print Report Button */}
          <button
            type="button"
            onClick={() => window.print()}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-lg bg-white hover:bg-slate-50 text-cv-text border border-cv-border font-semibold transition-all shadow-2xs"
            title="Open browser print dialog"
          >
            <Printer className="w-4 h-4 text-slate-600" />
            <span>Print Report</span>
          </button>

          {/* 2. Export as PDF Button */}
          <button
            type="button"
            onClick={handleExportPdf}
            disabled={exportingPdf}
            className="flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-cv-blue hover:bg-blue-700 text-white font-bold transition-all shadow-sm disabled:opacity-60 disabled:cursor-not-allowed"
            title="Download report directly as PDF"
          >
            {exportingPdf ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-white" />
                <span>Generating PDF...</span>
              </>
            ) : (
              <>
                <Download className="w-4 h-4 text-white" />
                <span>Export as PDF</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Main Printable / Exportable Document Container */}
      <div
        ref={reportRef}
        id="cyberval-report-document"
        className="p-8 sm:p-10 rounded-xl cyber-card border-cv-border bg-white space-y-8 font-mono text-xs text-cv-text print:bg-white print:text-black print:border-none print:shadow-none"
      >
        
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
            <h2 className="text-xl sm:text-2xl font-extrabold text-cv-text font-sans mt-2 tracking-tight print:text-black">
              Enterprise Cyber-Risk Quantification & Capital Allocation Report
            </h2>
            <p className="text-cv-muted text-xs mt-1 print:text-gray-600">
              Prepared for: Board of Directors & Chief Information Security Officer (CISO)
            </p>
          </div>

          <div className="text-right space-y-1 text-[11px] text-cv-muted print:text-gray-700">
            <div><strong>Date:</strong> {currentDate}</div>
            <div><strong>Frameworks:</strong> FAIR • RBI CSF • SEBI CSCRF • NIST • ISO</div>
            <div><strong>Status:</strong> <span className="text-cv-success font-bold print:text-black">AUDIT CERTIFIED</span></div>
          </div>
        </div>

        {/* Section 1: Executive KPI Scorecard */}
        <div className="space-y-3">
          <h3 className="text-sm font-bold text-cv-text font-sans uppercase tracking-wider flex items-center space-x-2 border-b border-cv-border pb-2 print:text-black print:border-black">
            <span className="w-2 h-2 rounded-full bg-cv-blue print:bg-black" />
            <span>1. Executive Cyber-Risk Financial Summary</span>
          </h3>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2">
            <div className="p-4 rounded-lg bg-cv-bg border border-cv-border print:border-gray-300 print:bg-gray-50">
              <span className="text-[10px] text-cv-muted uppercase block print:text-gray-600">Enterprise Risk Score</span>
              <div className="text-2xl font-black text-cv-danger font-sans mt-1 print:text-black">
                {execData?.enterpriseRiskScore} / 100
              </div>
              <span className="text-[10px] text-cv-muted print:text-gray-500">Benchmark Target: 42</span>
            </div>

            <div className="p-4 rounded-lg bg-cv-bg border border-cv-border print:border-gray-300 print:bg-gray-50">
              <span className="text-[10px] text-cv-muted uppercase block print:text-gray-600">Expected Annual Loss (EAL)</span>
              <div className="text-2xl font-black text-cv-text font-sans mt-1 print:text-black">
                {formatCurrency(execData?.expectedAnnualLoss)}
              </div>
              <span className="text-[10px] text-cv-muted print:text-gray-500">Annualized exposure</span>
            </div>

            <div className="p-4 rounded-lg bg-cv-bg border border-cv-border print:border-gray-300 print:bg-gray-50">
              <span className="text-[10px] text-cv-muted uppercase block print:text-gray-600">P95 Catastrophe VaR</span>
              <div className="text-2xl font-black text-cv-warning font-sans mt-1 print:text-black">
                {formatCurrency(execData?.p95Loss)}
              </div>
              <span className="text-[10px] text-cv-muted print:text-gray-500">1-in-20 year stress loss</span>
            </div>

            <div className="p-4 rounded-lg bg-cv-bg border border-cv-border print:border-gray-300 print:bg-gray-50">
              <span className="text-[10px] text-cv-muted uppercase block print:text-gray-600">Actionable Reduction</span>
              <div className="text-2xl font-black text-cv-success font-sans mt-1 print:text-black">
                {formatCurrency(execData?.potentialRiskReduction)}
              </div>
              <span className="text-[10px] text-cv-success font-bold print:text-black">400% Expected ROSI</span>
            </div>
          </div>
        </div>

        {/* Section 2: Key Executive Findings */}
        <div className="space-y-3">
          <h3 className="text-sm font-bold text-cv-text font-sans uppercase tracking-wider flex items-center space-x-2 border-b border-cv-border pb-2 print:text-black print:border-black">
            <span className="w-2 h-2 rounded-full bg-cv-danger print:bg-black" />
            <span>2. Key Findings & Primary Threat Drivers</span>
          </h3>

          <div className="p-4 rounded-lg bg-cv-bg border border-cv-border space-y-2.5 print:bg-gray-50 print:border-gray-300">
            <ul className="list-disc list-inside space-y-1.5 text-cv-muted print:text-black">
              <li>
                <strong className="text-cv-text">Critical Perimeter Exposure:</strong> Active weaponized exploit path on Citrix NetScaler (CVE-2023-4966) permits unauthenticated session memory dumping, leading directly to Domain Admin compromise and Core Banking DB (Oracle RAC) access within 3.5 hours.
              </li>
              <li>
                <strong className="text-cv-text">Financial Impact Concentration:</strong> The top 3 vulnerability paths account for <strong className="text-cv-text">82.0% ({formatCurrency(15.1)})</strong> of total annualized cyber exposure.
              </li>
              <li>
                <strong className="text-cv-text">Regulatory Compliance Posture:</strong> Current compliance stands at <strong className="text-cv-text">76.0% for RBI Cyber Security Framework</strong> and <strong className="text-cv-text">79.6% for SEBI CSCRF</strong>, with 5 control gaps identified in micro-segmentation and emergency patch SLAs.
              </li>
            </ul>
          </div>
        </div>

        {/* Section 3: Top Risk Contributors Table */}
        <div className="space-y-3">
          <h3 className="text-sm font-bold text-cv-text font-sans uppercase tracking-wider flex items-center space-x-2 border-b border-cv-border pb-2 print:text-black print:border-black">
            <span className="w-2 h-2 rounded-full bg-cv-warning print:bg-black" />
            <span>3. Top Risk Contributors (FAIR Ranked)</span>
          </h3>

          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs border border-cv-border print:border-black">
              <thead className="bg-cv-bg print:bg-gray-100 text-cv-muted print:text-black uppercase">
                <tr className="border-b border-cv-border print:border-black">
                  <th className="p-2.5">Risk Scenario & CVE</th>
                  <th className="p-2.5">Threat Actor / Vector</th>
                  <th className="p-2.5">Financial Exposure</th>
                  <th className="p-2.5">EAL Contribution</th>
                  <th className="p-2.5">% of Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-cv-border print:divide-gray-300">
                {execData?.topRiskContributors.map((rc) => (
                  <tr key={rc.id} className="hover:bg-cv-bg">
                    <td className="p-2.5">
                      <strong className="text-cv-text print:text-black">{rc.title}</strong>
                      <div className="text-[10px] text-cv-blue print:text-gray-700">{rc.cve} • {rc.severity}</div>
                    </td>
                    <td className="p-2.5 text-cv-muted print:text-black">{rc.threatActor}</td>
                    <td className="p-2.5 text-cv-text print:text-black">{formatCurrency(rc.financialExposure)}</td>
                    <td className="p-2.5 text-cv-danger font-bold print:text-black">{formatCurrency(rc.ealContribution)}</td>
                    <td className="p-2.5 text-cv-text font-bold print:text-black">{rc.percentage}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Section 4: Recommended Security Investment Portfolio (ROSI-Ranked) */}
        <div className="space-y-3">
          <h3 className="text-sm font-bold text-cv-text font-sans uppercase tracking-wider flex items-center space-x-2 border-b border-cv-border pb-2 print:text-black print:border-black">
            <span className="w-2 h-2 rounded-full bg-cv-success print:bg-black" />
            <span>4. Security Investment Portfolio & Capital Allocation</span>
          </h3>

          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs border border-cv-border print:border-black">
              <thead className="bg-cv-bg print:bg-gray-100 text-cv-muted print:text-black uppercase">
                <tr className="border-b border-cv-border print:border-black">
                  <th className="p-2.5">Rank & Initiative</th>
                  <th className="p-2.5">Domain</th>
                  <th className="p-2.5">Capital Cost</th>
                  <th className="p-2.5">EAL Reduction</th>
                  <th className="p-2.5">ROSI %</th>
                  <th className="p-2.5">Payback Period</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-cv-border print:divide-gray-300">
                {investmentData?.recommendedInitiatives.map((init) => (
                  <tr key={init.id} className="hover:bg-cv-bg">
                    <td className="p-2.5 font-bold text-cv-text print:text-black">#{init.priorityRank} {init.title}</td>
                    <td className="p-2.5 text-cv-muted print:text-gray-700">{init.domain}</td>
                    <td className="p-2.5 font-bold text-cv-text print:text-black">{formatCurrency(init.cost)}</td>
                    <td className="p-2.5 font-bold text-cv-success print:text-black">-{formatCurrency(init.riskReduction)}</td>
                    <td className="p-2.5 font-bold text-cv-blue print:text-black">{init.rosi}%</td>
                    <td className="p-2.5 text-cv-muted print:text-black">{init.paybackPeriod}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="p-3 rounded-lg bg-cv-successBg border border-green-200 text-[11px] text-cv-success print:bg-gray-50 print:border-black print:text-black">
            ⚡ <strong>Board Recommendation:</strong> Approving the top 3 initiatives (Hardware MFA MC-04, Micro-segmentation MC-11, Patching MC-08) consumes <strong>₹1.30 Cr</strong> of budget to remove <strong>₹6.5 Cr of annual risk</strong> (ROSI 400%).
          </div>
        </div>

        {/* Section 5: Regulatory Compliance Status */}
        <div className="space-y-3">
          <h3 className="text-sm font-bold text-cv-text font-sans uppercase tracking-wider flex items-center space-x-2 border-b border-cv-border pb-2 print:text-black print:border-black">
            <span className="w-2 h-2 rounded-full bg-cv-blue print:bg-black" />
            <span>5. Regulatory Framework Compliance Matrix</span>
          </h3>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {complianceData?.frameworkStats.map((fw, idx) => (
              <div key={idx} className="p-3 rounded-lg bg-cv-bg border border-cv-border print:bg-gray-50 print:border-gray-300">
                <span className="text-[10px] text-cv-muted block truncate print:text-gray-700">{fw.name}</span>
                <span className="text-lg font-bold text-cv-success font-sans print:text-black">{fw.score}%</span>
                <div className="text-[10px] text-cv-muted mt-1 print:text-gray-600">{fw.compliant}/{fw.totalControls} Controls</div>
              </div>
            ))}
          </div>
        </div>

        {/* Signatures Footer */}
        <div className="pt-8 border-t border-cv-border print:border-black flex flex-col sm:flex-row justify-between items-end gap-6 text-[11px] text-cv-muted print:text-gray-700">
          <div>
            <p className="font-bold text-cv-text print:text-black">CYBERVAL Continuous Risk Intelligence Platform</p>
            <p className="text-[10px]">Telemetry Source: Live Production Sensors (EDR, SIEM, CSPM, WAF)</p>
          </div>

          <div className="flex space-x-8 text-center">
            <div className="border-t border-cv-border print:border-black pt-1 px-4">
              <p className="font-bold text-cv-text print:text-black">Chief Information Security Officer</p>
              <p className="text-[10px]">CISO Sign-off</p>
            </div>
            <div className="border-t border-cv-border print:border-black pt-1 px-4">
              <p className="font-bold text-cv-text print:text-black">Chief Financial Officer</p>
              <p className="text-[10px]">CFO Capital Approval</p>
            </div>
          </div>
        </div>

      </div>

    </div>
  );
}
