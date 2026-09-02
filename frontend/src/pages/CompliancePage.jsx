import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  FileCheck,
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
import { NO_DATA } from '../utils/formatters';

export default function CompliancePage() {
  const { formatCurrency, refreshKey } = useTelemetry();
  const [complianceStats, setComplianceStats] = useState([]);
  const [masterControls, setMasterControls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [selectedFramework, setSelectedFramework] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedControl, setSelectedControl] = useState(null);

  useEffect(() => {
    async function loadCompliance() {
      try {
        setLoading(true);
        const [coverageRes, controlsRes] = await Promise.all([
          complianceApi.getComplianceCoverage(),
          complianceApi.getControls(),
        ]);
        setComplianceStats(coverageRes || []);
        setMasterControls(controlsRes || []);
        setError(null);
      } catch (err) {
        console.error('Error loading compliance master mapping:', err);
        setError('Failed to fetch regulatory compliance telemetry from backend.');
      } finally {
        setLoading(false);
      }
    }
    loadCompliance();
  }, [refreshKey]);

  if (loading) return <LoadingSpinner text="Harmonizing Master Controls Across NIST, ISO, CIS, RBI, SEBI..." />;
  if (error) {
    return (
      <div className="p-8 text-center text-cv-danger border border-red-200 rounded-lg bg-red-50 font-mono">
        <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-cv-danger" />
        <p>{error}</p>
      </div>
    );
  }

  // Calculate overall audit readiness score
  const totalMapped = complianceStats.reduce((acc, c) => acc + (c.mapped_controls || 0), 0);
  const totalControls = complianceStats.reduce((acc, c) => acc + (c.total_controls || 0), 0);
  const overallCoveragePct = totalControls > 0 ? ((totalMapped / totalControls) * 100).toFixed(1) : NO_DATA;

  // Filter master controls
  const filteredControls = masterControls.filter((ctrl) => {
    const matchesSearch =
      ctrl.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ctrl.description?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  return (
    <div className="space-y-6">
      
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-lg cyber-card border-cv-border">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cv-successBg text-cv-success border border-green-200">
              UNIFIED COMPLIANCE ENGINE
            </span>
            <span className="text-xs font-mono text-cv-muted">
              Live PostgreSQL Framework Mappings (`/api/compliance`)
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-cv-text mt-1 tracking-tight">
            Regulatory Compliance & Master Control Mapping
          </h1>
          <p className="text-xs sm:text-sm text-cv-muted mt-0.5">
            Cross-regulatory compliance harmonized across NIST CSF, ISO/IEC 27001, CIS Controls, RBI CSF, and SEBI CSCRF.
          </p>
        </div>

        <div className="flex items-center space-x-2 font-mono text-xs">
          <div className="px-3 py-2 rounded-lg bg-cv-bg border border-cv-border text-cv-text">
            AUDIT COVERAGE: <strong className="text-cv-success">{overallCoveragePct}%</strong>
          </div>
        </div>
      </div>

      {/* Regulatory Framework Scorecards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 font-mono">
        {complianceStats.map((fw) => {
          const pct = fw.total_controls > 0 ? Math.round((fw.mapped_controls / fw.total_controls) * 100) : 0;
          return (
            <div
              key={fw.framework}
              onClick={() => setSelectedFramework(fw.framework)}
              className={`p-3.5 rounded-lg border transition-all cursor-pointer ${
                selectedFramework === fw.framework
                  ? 'border-cv-blue bg-cv-blueLight/30 shadow-card'
                  : 'border-cv-border bg-white hover:border-slate-300'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-cv-text font-sans truncate">{fw.framework}</span>
                <span className="text-[10px] text-cv-success font-bold">{pct}%</span>
              </div>
              <div className="mt-2 flex items-baseline justify-between text-[11px] text-cv-muted">
                <span>Mapped:</span>
                <strong className="text-cv-text">{fw.mapped_controls} / {fw.total_controls}</strong>
              </div>
              <div className="w-full bg-cv-bg rounded-full h-1.5 overflow-hidden mt-1.5">
                <div className="bg-cv-success h-full rounded-full" style={{ width: `${pct}%` }} />
              </div>
            </div>
          );
        })}
        {complianceStats.length === 0 && (
          <div className="col-span-5 p-8 text-center text-cv-muted font-mono text-xs">
            {NO_DATA} (No regulatory frameworks mapped in database)
          </div>
        )}
      </div>

      {/* Master Controls Inventory Table */}
      <div className="cyber-card rounded-lg border-cv-border p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-cv-border pb-3">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-cv-blue" />
            <h3 className="text-sm font-sans font-semibold text-cv-text">
              MASTER CONTROLS ({filteredControls.length})
            </h3>
          </div>

          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-cv-muted" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search controls by name or description..."
              className="pl-8 pr-3 py-1.5 rounded bg-cv-bg border border-cv-border text-xs font-mono text-cv-text focus:outline-none focus:border-cv-blue"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="border-b border-cv-border text-cv-muted text-[11px]">
                <th className="pb-3">CONTROL ID</th>
                <th className="pb-3">NAME</th>
                <th className="pb-3">DESCRIPTION</th>
                <th className="pb-3">EFFECTIVENESS</th>
                <th className="pb-3">STATUS</th>
                <th className="pb-3">AUDIT DETAIL</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-cv-border">
              {filteredControls.map((ctrl) => (
                <tr key={ctrl.id} className="hover:bg-cv-bg/50">
                  <td className="py-3 font-bold text-cv-blue">MC-{String(ctrl.id).padStart(2, '0')}</td>
                  <td className="py-3 font-bold text-cv-text">{ctrl.name}</td>
                  <td className="py-3 text-cv-muted max-w-md truncate">{ctrl.description}</td>
                  <td className="py-3 font-bold text-cv-success">
                    {(Number(ctrl.effectiveness) * 100).toFixed(0)}%
                  </td>
                  <td className="py-3">
                    <Badge variant="success">
                      {ctrl.status?.toUpperCase() || 'ACTIVE'}
                    </Badge>
                  </td>
                  <td className="py-3">
                    <button
                      onClick={() => setSelectedControl(ctrl)}
                      className="text-cv-blue hover:underline font-bold"
                    >
                      View Evidence
                    </button>
                  </td>
                </tr>
              ))}
              {filteredControls.length === 0 && (
                <tr>
                  <td colSpan="6" className="py-8 text-center text-cv-muted">
                    {NO_DATA}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Control Detail / Evidence Modal */}
      {selectedControl && (
        <Modal
          isOpen={!!selectedControl}
          onClose={() => setSelectedControl(null)}
          title={`Master Control Evidence: ${selectedControl.name}`}
          size="md"
        >
          <div className="space-y-4 font-mono text-xs">
            <div className="p-3 bg-cv-bg rounded border border-cv-border space-y-1">
              <div className="text-cv-muted">Control Identifier: <strong className="text-cv-text">MC-{String(selectedControl.id).padStart(2, '0')}</strong></div>
              <div className="text-cv-muted">Mitigation Effectiveness: <strong className="text-cv-success">{(Number(selectedControl.effectiveness) * 100).toFixed(0)}%</strong></div>
              <div className="text-cv-muted">Implementation Status: <strong className="text-cv-text uppercase">{selectedControl.status}</strong></div>
            </div>

            <div>
              <span className="font-bold text-cv-text block mb-1">Description:</span>
              <p className="text-cv-muted font-sans text-xs bg-cv-bg p-2.5 rounded border border-cv-border">
                {selectedControl.description}
              </p>
            </div>

            <div>
              <span className="font-bold text-cv-text block mb-1">Harmonized Framework Mappings:</span>
              <div className="flex flex-wrap gap-1.5">
                {complianceStats.map((fw) => (
                  <span key={fw.framework} className="px-2 py-1 rounded bg-green-50 text-cv-success border border-green-200 text-[10px] font-bold">
                    ✓ {fw.framework}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </Modal>
      )}

    </div>
  );
}
