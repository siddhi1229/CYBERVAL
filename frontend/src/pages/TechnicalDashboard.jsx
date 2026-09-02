import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Cpu,
  ShieldAlert,
  AlertTriangle,
  Server,
  Layers,
  Bug,
  ShieldCheck,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  Network,
  Activity,
  Terminal,
  UserCheck,
  Zap
} from 'lucide-react';
import MetricCard from '../components/common/MetricCard';
import Badge from '../components/common/Badge';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { useTelemetry } from '../context/TelemetryContext';
import { technicalApi } from '../api/technicalApi';
import { NO_DATA } from '../utils/formatters';

export default function TechnicalDashboard() {
  const navigate = useNavigate();
  const { formatCurrency, refreshKey } = useTelemetry();

  const [assets, setAssets] = useState([]);
  const [vulnerabilities, setVulnerabilities] = useState([]);
  const [selectedAssetId, setSelectedAssetId] = useState(null);
  const [correlatedData, setCorrelatedData] = useState(null);
  const [loadingCorrelation, setLoadingCorrelation] = useState(false);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [searchFilter, setSearchFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [criticalityFilter, setCriticalityFilter] = useState('ALL');

  useEffect(() => {
    async function loadTechnicalData() {
      try {
        setLoading(true);
        const [assetsRes, vulnsRes] = await Promise.all([
          technicalApi.getAssets({ limit: 200 }),
          technicalApi.getVulnerabilities(),
        ]);
        setAssets(assetsRes || []);
        setVulnerabilities(vulnsRes || []);
        if (assetsRes && assetsRes.length > 0) {
          setSelectedAssetId(assetsRes[0].id);
        }
        setError(null);
      } catch (err) {
        console.error('Error loading technical dashboard:', err);
        setError('Failed to fetch asset inventory and vulnerability telemetry.');
      } finally {
        setLoading(false);
      }
    }
    loadTechnicalData();
  }, [refreshKey]);

  // Load 360-degree security correlation when an asset is selected
  useEffect(() => {
    if (!selectedAssetId) return;
    async function loadCorrelation() {
      try {
        setLoadingCorrelation(true);
        const res = await technicalApi.getAssetCorrelation(selectedAssetId);
        setCorrelatedData(res);
      } catch (err) {
        console.warn(`Could not load correlation for asset ${selectedAssetId}:`, err.message);
        setCorrelatedData(null);
      } finally {
        setLoadingCorrelation(false);
      }
    }
    loadCorrelation();
  }, [selectedAssetId]);

  if (loading) return <LoadingSpinner text="Ingesting Normalized Asset Inventory & Vulnerabilities..." />;
  if (error) {
    return (
      <div className="p-8 text-center text-cv-danger border border-red-200 rounded-lg bg-red-50 font-mono">
        <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-cv-danger" />
        <p>{error}</p>
      </div>
    );
  }

  // Filter assets
  const filteredAssets = assets.filter((a) => {
    const matchesSearch =
      (a.name && a.name.toLowerCase().includes(searchFilter.toLowerCase())) ||
      (a.owner && a.owner.toLowerCase().includes(searchFilter.toLowerCase())) ||
      (a.ip_address && a.ip_address.toLowerCase().includes(searchFilter.toLowerCase()));

    const matchesType = typeFilter === 'ALL' || a.asset_type?.toLowerCase() === typeFilter.toLowerCase();
    const matchesCrit = criticalityFilter === 'ALL' || a.criticality?.toLowerCase() === criticalityFilter.toLowerCase();

    return matchesSearch && matchesType && matchesCrit;
  });

  const criticalVulnsCount = vulnerabilities.filter((v) => v.severity?.toLowerCase() === 'critical').length;
  const kevExploitedCount = vulnerabilities.filter((v) => v.known_exploited).length;
  const exposedAssetsCount = assets.filter((a) => a.internet_exposed).length;

  return (
    <div className="space-y-6">
      
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-lg cyber-card border-cv-border">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cv-blueLight text-cv-blue border border-blue-200">
              TECHNICAL SECURITY TELEMETRY
            </span>
            <span className="text-xs font-mono text-cv-muted">
              P1 Normalized Ingestion • PostgreSQL Master Store
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-cv-text mt-1 tracking-tight">
            Technical Asset Inventory & 360° Security Correlation
          </h1>
          <p className="text-xs sm:text-sm text-cv-muted mt-0.5">
            Cross-telemetry convergence across Asset Inventory, NVD/CISA KEV, SIEM Events, EDR Processes, and CSPM Findings.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => navigate('/attack-graph')}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-lg bg-cv-blueLight border border-blue-200 text-cv-blue hover:bg-blue-100 font-mono text-xs font-semibold shadow-sm transition-all"
          >
            <Network className="w-4 h-4 text-cv-blue" />
            <span>VIEW IN ATTACK GRAPH</span>
          </button>
        </div>
      </div>

      {/* KPI Overview Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Assets"
          value={assets.length}
          unit="Normalized"
          subtitle={`${exposedAssetsCount} internet-facing`}
          icon={Server}
          variant="cyan"
          technicalBadge="Assets"
          technicalTooltip="Normalized inventory synced from enterprise infrastructure."
        />

        <MetricCard
          title="Active Vulnerabilities"
          value={vulnerabilities.length}
          unit="CVEs"
          subtitle={`${criticalVulnsCount} critical severity`}
          icon={Bug}
          variant="critical"
          technicalBadge="CVE"
          technicalTooltip="Vulnerabilities correlated with NVD and CVSS scoring."
        />

        <MetricCard
          title="CISA KEV Exploited"
          value={kevExploitedCount}
          unit="In-the-Wild"
          subtitle="Actively exploited catalog"
          icon={ShieldAlert}
          variant="warning"
          technicalBadge="KEV"
          technicalTooltip="CISA Known Exploited Vulnerabilities catalog matches."
        />

        <MetricCard
          title="Internet Exposed"
          value={exposedAssetsCount}
          unit="Hosts"
          subtitle="Public attack surface"
          icon={Zap}
          variant="danger"
          technicalBadge="Ingress"
          technicalTooltip="Assets with direct ingress accessibility from the public internet."
        />
      </div>

      {/* Main Content Split: Asset Table & 360-Degree Correlation Pane */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Asset Selection Table */}
        <div className="lg:col-span-7 cyber-card rounded-lg border-cv-border p-5 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-cv-border pb-3">
            <h3 className="text-sm font-sans font-semibold text-cv-text flex items-center space-x-2">
              <Server className="w-4 h-4 text-cv-blue" />
              <span>NORMALIZED ENTERPRISE ASSETS ({filteredAssets.length})</span>
            </h3>
            
            {/* Search Input */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-cv-muted" />
              <input
                type="text"
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                placeholder="Filter by name, IP, or owner..."
                className="pl-8 pr-3 py-1.5 rounded bg-cv-bg border border-cv-border text-xs font-mono text-cv-text focus:outline-none focus:border-cv-blue"
              />
            </div>
          </div>

          <div className="overflow-y-auto max-h-[520px]">
            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="border-b border-cv-border text-cv-muted text-[11px] sticky top-0 bg-white">
                  <th className="pb-2">NAME</th>
                  <th className="pb-2">TYPE</th>
                  <th className="pb-2">CRITICALITY</th>
                  <th className="pb-2">SURFACE</th>
                  <th className="pb-2">OWNER</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-cv-border">
                {filteredAssets.map((asset) => {
                  const isSelected = asset.id === selectedAssetId;
                  return (
                    <tr
                      key={asset.id}
                      onClick={() => setSelectedAssetId(asset.id)}
                      className={`cursor-pointer transition-colors ${
                        isSelected ? 'bg-cv-blueLight/50 font-bold' : 'hover:bg-cv-bg/50'
                      }`}
                    >
                      <td className="py-2.5 text-cv-text">
                        <span className="flex items-center space-x-1.5">
                          <span className={`w-1.5 h-1.5 rounded-full ${asset.internet_exposed ? 'bg-cv-danger' : 'bg-cv-success'}`} />
                          <span>{asset.name}</span>
                        </span>
                      </td>
                      <td className="py-2.5 text-cv-muted capitalize">{asset.asset_type}</td>
                      <td className="py-2.5">
                        <Badge variant={asset.criticality?.toLowerCase() === 'critical' ? 'critical' : 'warning'}>
                          {asset.criticality?.toUpperCase()}
                        </Badge>
                      </td>
                      <td className="py-2.5">
                        {asset.internet_exposed ? (
                          <span className="text-[10px] text-cv-danger font-bold">INTERNET</span>
                        ) : (
                          <span className="text-[10px] text-cv-muted">INTERNAL</span>
                        )}
                      </td>
                      <td className="py-2.5 text-cv-muted truncate max-w-[100px]">{asset.owner}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column: 360-Degree Security Correlation View */}
        <div className="lg:col-span-5 cyber-card rounded-lg border-cv-border p-5 space-y-4">
          <div className="border-b border-cv-border pb-3 flex items-center justify-between">
            <h3 className="text-sm font-sans font-semibold text-cv-text flex items-center space-x-2">
              <Activity className="w-4 h-4 text-cv-danger" />
              <span>360° TELEMETRY CORRELATION</span>
            </h3>
            {correlatedData && (
              <Badge variant={correlatedData.converged_risk_level === 'critical' ? 'critical' : 'warning'}>
                {correlatedData.converged_risk_level?.toUpperCase()} RISK
              </Badge>
            )}
          </div>

          {loadingCorrelation ? (
            <div className="py-20 text-center">
              <LoadingSpinner text="Correlating telemetry across SIEM, EDR, CSPM, and IAM..." />
            </div>
          ) : correlatedData ? (
            <div className="space-y-4 font-mono text-xs">
              <div>
                <h4 className="text-base font-bold text-cv-text font-sans">{correlatedData.asset_name}</h4>
                <p className="text-[11px] text-cv-muted">
                  Environment: <strong className="text-cv-text">{correlatedData.environment}</strong> • Owner: <strong className="text-cv-text">{correlatedData.owner}</strong>
                </p>
                {correlatedData.graph_risk_score != null && (
                  <p className="text-[11px] text-cv-danger mt-0.5">
                    Graph Risk Priority Score: <strong>{correlatedData.graph_risk_score.toFixed(1)} / 100</strong>
                  </p>
                )}
              </div>

              {/* Converged Risk Factors */}
              {correlatedData.risk_factors?.length > 0 && (
                <div className="p-3 rounded-lg bg-red-50 border border-red-200 space-y-1.5">
                  <span className="text-[10px] uppercase font-bold text-cv-danger flex items-center space-x-1">
                    <ShieldAlert className="w-3.5 h-3.5" />
                    <span>Converged Risk Indicators</span>
                  </span>
                  <ul className="list-disc list-inside space-y-1 text-[11px] text-cv-text">
                    {correlatedData.risk_factors.map((rf, idx) => (
                      <li key={idx} className="text-red-950 font-medium">{rf}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Correlated Multi-Source Signals */}
              <div className="space-y-2">
                
                {/* Vulnerabilities */}
                <div className="p-2.5 rounded bg-cv-bg border border-cv-border">
                  <div className="flex justify-between font-bold text-[11px] text-cv-text mb-1">
                    <span>Vulnerabilities (CVEs)</span>
                    <span className="text-cv-danger">{correlatedData.vulnerabilities?.length || 0}</span>
                  </div>
                  {correlatedData.vulnerabilities?.map((v, i) => (
                    <div key={i} className="text-[10px] text-cv-muted flex justify-between py-0.5">
                      <span className="text-cv-blue font-bold">{v.cve_id}</span>
                      <span className="text-cv-danger font-bold">CVSS {v.cvss_score}</span>
                    </div>
                  ))}
                  {(!correlatedData.vulnerabilities || correlatedData.vulnerabilities.length === 0) && (
                    <span className="text-[10px] text-cv-muted italic">{NO_DATA}</span>
                  )}
                </div>

                {/* SIEM Alerts */}
                <div className="p-2.5 rounded bg-cv-bg border border-cv-border">
                  <div className="flex justify-between font-bold text-[11px] text-cv-text mb-1">
                    <span>SIEM Events (T1110, Brute Force)</span>
                    <span className="text-cv-warning">{correlatedData.siem_events?.length || 0}</span>
                  </div>
                  {correlatedData.siem_events?.slice(0, 3).map((ev, i) => (
                    <div key={i} className="text-[10px] text-cv-muted flex justify-between py-0.5">
                      <span>{ev.event_type}</span>
                      <span className="text-cv-warning font-bold">{ev.severity?.toUpperCase()}</span>
                    </div>
                  ))}
                </div>

                {/* EDR Events */}
                <div className="p-2.5 rounded bg-cv-bg border border-cv-border">
                  <div className="flex justify-between font-bold text-[11px] text-cv-text mb-1">
                    <span>EDR Malicious Execution (T1003, Mimikatz)</span>
                    <span className="text-cv-danger">{correlatedData.edr_events?.length || 0}</span>
                  </div>
                  {correlatedData.edr_events?.slice(0, 3).map((edr, i) => (
                    <div key={i} className="text-[10px] text-cv-muted flex justify-between py-0.5">
                      <span>{edr.event_type}</span>
                      <span className="text-cv-danger font-bold">{edr.severity?.toUpperCase()}</span>
                    </div>
                  ))}
                </div>

                {/* CSPM Misconfigurations */}
                <div className="p-2.5 rounded bg-cv-bg border border-cv-border">
                  <div className="flex justify-between font-bold text-[11px] text-cv-text mb-1">
                    <span>CSPM Cloud Misconfigurations</span>
                    <span className="text-cv-danger">{correlatedData.cspm_findings?.length || 0}</span>
                  </div>
                  {correlatedData.cspm_findings?.slice(0, 3).map((c, i) => (
                    <div key={i} className="text-[10px] text-cv-muted flex justify-between py-0.5">
                      <span>{c.event_type}</span>
                      <span className="text-cv-danger font-bold">{c.severity?.toUpperCase()}</span>
                    </div>
                  ))}
                </div>

              </div>

            </div>
          ) : (
            <div className="py-20 text-center font-mono text-xs text-cv-muted">
              Select an asset on the left to inspect multi-source telemetry convergence.
            </div>
          )}
        </div>

      </div>

    </div>
  );
}
