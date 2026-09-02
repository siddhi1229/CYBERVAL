import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Cpu,
  ShieldAlert,
  AlertTriangle,
  Server,
  Layers,
  ChevronRight,
  Bug,
  ShieldCheck,
  Clock,
  ExternalLink,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  Network
} from 'lucide-react';
import MetricCard from '../components/common/MetricCard';
import Badge from '../components/common/Badge';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { useTelemetry } from '../context/TelemetryContext';
import { technicalApi } from '../api/technicalApi';

export default function TechnicalDashboard() {
  const navigate = useNavigate();
  const { formatCurrency, refreshKey } = useTelemetry();
  const [data, setData] = useState(null);
  const [drilldownTree, setDrilldownTree] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Drilldown selection state: 6 levels
  // [Enterprise -> Business Unit -> Business Service -> Asset -> Vulnerability -> Control]
  const [selectedBUIndex, setSelectedBUIndex] = useState(0);
  const [selectedServiceIndex, setSelectedServiceIndex] = useState(0);
  const [selectedAssetIndex, setSelectedAssetIndex] = useState(0);
  const [selectedVulnIndex, setSelectedVulnIndex] = useState(0);

  const [searchFilter, setSearchFilter] = useState('');

  useEffect(() => {
    async function loadTechnicalData() {
      try {
        setLoading(true);
        const [overviewRes, treeRes] = await Promise.all([
          technicalApi.getOverview(),
          technicalApi.getDrilldownTree()
        ]);
        setData(overviewRes);
        setDrilldownTree(treeRes);
        setError(null);
      } catch (err) {
        console.error('Error loading technical dashboard:', err);
        setError('Failed to fetch technical risk data.');
      } finally {
        setLoading(false);
      }
    }
    loadTechnicalData();
  }, [refreshKey]);

  if (loading) return <LoadingSpinner text="Ingesting Vulnerability & Asset Telemetry..." />;
  if (error || !data || !drilldownTree) {
    return (
      <div className="p-8 text-center text-cv-danger border border-red-200 rounded-lg bg-red-50 font-mono">
        <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-cv-danger" />
        <p>{error || 'Technical telemetry unavailable.'}</p>
      </div>
    );
  }

  // Active drilldown references
  const currentBU = drilldownTree.units?.[selectedBUIndex] || drilldownTree.units?.[0];
  const currentService = currentBU?.services?.[selectedServiceIndex] || currentBU?.services?.[0];
  const currentAsset = currentService?.assets?.[selectedAssetIndex] || currentService?.assets?.[0];
  const currentVuln = currentAsset?.vulnerabilities?.[selectedVulnIndex] || currentAsset?.vulnerabilities?.[0];

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-lg cyber-card border-cv-border">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cv-blueLight text-cv-blue border border-blue-200">
              TECHNICAL INTELLIGENCE
            </span>
            <span className="text-xs font-mono text-cv-muted">
              6-Tier Hierarchical Drilldown • Crown Jewels & Weaponized Exploits
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-cv-text mt-1 tracking-tight">
            Technical Cyber-Risk & Remediation Backlog
          </h1>
          <p className="text-xs sm:text-sm text-cv-muted mt-0.5">
            Real-time vulnerability weaponization, asset risk scoring, and Master Control remediation SLAs.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => navigate('/attack-graph')}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-lg bg-cv-blueLight border border-blue-200 text-cv-blue hover:bg-blue-100 font-mono text-xs font-semibold shadow-sm transition-all"
          >
            <Network className="w-4 h-4 text-cv-blue" />
            <span>VIEW ATTACK GRAPH</span>
          </button>
        </div>
      </div>

      {/* Technical KPI Overview Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Critical Vulnerabilities"
          value={data.overview.criticalVulnerabilities}
          unit="P0 CVEs"
          subtitle="CVSS > 9.0 (EPSS > 85%)"
          delta={2}
          deltaType="positive_is_good"
          icon={Bug}
          variant="critical"
          badge="WEAPONIZED"
        />

        <MetricCard
          title="Affected Assets"
          value={data.overview.affectedAssets}
          unit="Hosts"
          subtitle="2 Crown Jewel DB Clusters"
          delta={-4}
          deltaType="negative_is_good"
          icon={Server}
          variant="warning"
          badge="TIER 1 & 2"
        />

        <MetricCard
          title="Active Attack Paths"
          value={data.overview.activeAttackPaths}
          unit="Chains"
          subtitle="Fastest: 3.5h to Core DB"
          delta={1}
          deltaType="positive_is_good"
          icon={Network}
          variant="cyan"
          badge="LATERAL"
        />

        <MetricCard
          title="Control Effectiveness"
          value={`${data.overview.controlEffectivenessScore}%`}
          subtitle="19 Control Gaps Identified"
          delta={-3.2}
          deltaType="negative_is_good"
          icon={ShieldCheck}
          variant="purple"
          badge="TELEMETRY"
        />
      </div>

      {/* 6-Level Hierarchy Drilldown Interface */}
      <div className="cyber-card rounded-lg p-5 border-cv-border space-y-4">
        
        {/* Drilldown Header & Breadcrumbs */}
        <div className="border-b border-cv-border pb-3 flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-sans font-semibold text-cv-text flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-cv-blue" />
              <span>6-LEVEL ENTERPRISE HIERARCHY DRILLDOWN</span>
            </h3>
            <p className="text-xs text-cv-muted">
              Enterprise → Business Unit → Business Service → Asset → Vulnerability → Control
            </p>
          </div>

          {/* Dynamic Breadcrumbs */}
          <div className="flex flex-wrap items-center gap-1.5 font-mono text-[11px] bg-cv-bg p-2 rounded-lg border border-cv-border">
            <span className="text-cv-text font-bold">Enterprise</span>
            <ChevronRight className="w-3 h-3 text-cv-muted" />
            <span className="text-cv-blue font-bold">{currentBU?.name}</span>
            <ChevronRight className="w-3 h-3 text-cv-muted" />
            <span className="text-cv-success font-bold">{currentService?.name}</span>
            <ChevronRight className="w-3 h-3 text-cv-muted" />
            <span className="text-cv-warning font-bold">{currentAsset?.name}</span>
            <ChevronRight className="w-3 h-3 text-cv-muted" />
            <span className="text-cv-danger font-bold">{currentVuln?.cve}</span>
          </div>
        </div>

        {/* Multi-Level Selector Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4 font-mono text-xs">
          
          {/* Level 2: Business Units */}
          <div className="space-y-2 p-3 rounded-lg bg-cv-bg border border-cv-border">
            <div className="text-cv-muted font-bold uppercase text-[10px] tracking-wider flex items-center justify-between">
              <span>Level 2: Business Unit</span>
              <span className="text-cv-blue font-bold">{drilldownTree.units.length} Units</span>
            </div>
            <div className="space-y-1.5">
              {drilldownTree.units.map((bu, idx) => (
                <button
                  key={bu.id}
                  onClick={() => {
                    setSelectedBUIndex(idx);
                    setSelectedServiceIndex(0);
                    setSelectedAssetIndex(0);
                    setSelectedVulnIndex(0);
                  }}
                  className={`w-full text-left p-2.5 rounded-lg border transition-all ${
                    selectedBUIndex === idx
                      ? 'bg-white border-cv-blue text-cv-text shadow-card font-semibold'
                      : 'bg-white/60 border-cv-border text-cv-muted hover:text-cv-text hover:bg-white'
                  }`}
                >
                  <div className="font-semibold truncate text-cv-text">{bu.name}</div>
                  <div className="flex items-center justify-between text-[10px] mt-1 text-cv-muted">
                    <span>Risk: <strong className="text-cv-danger">{bu.riskScore}</strong></span>
                    <span>EAL: <strong className="text-cv-text">{formatCurrency(bu.eal)}</strong></span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Level 3: Business Services */}
          <div className="space-y-2 p-3 rounded-lg bg-cv-bg border border-cv-border">
            <div className="text-cv-muted font-bold uppercase text-[10px] tracking-wider flex items-center justify-between">
              <span>Level 3: Business Service</span>
              <span className="text-cv-success font-bold">{currentBU?.services?.length || 0} Services</span>
            </div>
            <div className="space-y-1.5">
              {currentBU?.services?.map((svc, idx) => (
                <button
                  key={svc.id}
                  onClick={() => {
                    setSelectedServiceIndex(idx);
                    setSelectedAssetIndex(0);
                    setSelectedVulnIndex(0);
                  }}
                  className={`w-full text-left p-2.5 rounded-lg border transition-all ${
                    selectedServiceIndex === idx
                      ? 'bg-white border-green-500 text-cv-text shadow-card font-semibold'
                      : 'bg-white/60 border-cv-border text-cv-muted hover:text-cv-text hover:bg-white'
                  }`}
                >
                  <div className="font-semibold truncate text-cv-text">{svc.name}</div>
                  <div className="flex items-center justify-between text-[10px] mt-1 text-cv-muted">
                    <span>Risk: <strong className="text-cv-danger">{svc.riskScore}</strong></span>
                    <span>Assets: <strong className="text-cv-text">{svc.assets?.length || 0}</strong></span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Level 4: Assets */}
          <div className="space-y-2 p-3 rounded-lg bg-cv-bg border border-cv-border">
            <div className="text-cv-muted font-bold uppercase text-[10px] tracking-wider flex items-center justify-between">
              <span>Level 4: Affected Asset</span>
              <span className="text-cv-warning font-bold">{currentService?.assets?.length || 0} Assets</span>
            </div>
            <div className="space-y-1.5">
              {currentService?.assets?.map((ast, idx) => (
                <button
                  key={ast.id}
                  onClick={() => {
                    setSelectedAssetIndex(idx);
                    setSelectedVulnIndex(0);
                  }}
                  className={`w-full text-left p-2.5 rounded-lg border transition-all ${
                    selectedAssetIndex === idx
                      ? 'bg-white border-amber-500 text-cv-text shadow-card font-semibold'
                      : 'bg-white/60 border-cv-border text-cv-muted hover:text-cv-text hover:bg-white'
                  }`}
                >
                  <div className="font-semibold truncate text-cv-text">{ast.name}</div>
                  <div className="text-[10px] text-cv-blue font-semibold">{ast.ip} • {ast.type}</div>
                  <div className="flex items-center justify-between text-[10px] mt-1 text-cv-muted">
                    <span className="text-cv-danger font-bold">{ast.criticality}</span>
                    <span>EAL: {formatCurrency(ast.eal)}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Level 5: Vulnerabilities */}
          <div className="space-y-2 p-3 rounded-lg bg-cv-bg border border-cv-border">
            <div className="text-cv-muted font-bold uppercase text-[10px] tracking-wider flex items-center justify-between">
              <span>Level 5: Vulnerability</span>
              <span className="text-cv-danger font-bold">{currentAsset?.vulnerabilities?.length || 0} CVEs</span>
            </div>
            <div className="space-y-1.5">
              {currentAsset?.vulnerabilities?.map((vuln, idx) => (
                <button
                  key={vuln.id}
                  onClick={() => setSelectedVulnIndex(idx)}
                  className={`w-full text-left p-2.5 rounded-lg border transition-all ${
                    selectedVulnIndex === idx
                      ? 'bg-white border-red-500 text-cv-text shadow-card font-semibold'
                      : 'bg-white/60 border-cv-border text-cv-muted hover:text-cv-text hover:bg-white'
                  }`}
                >
                  <div className="font-bold text-cv-danger">{vuln.cve}</div>
                  <div className="text-[10px] text-cv-text truncate">{vuln.name}</div>
                  <div className="flex items-center justify-between text-[10px] mt-1 text-cv-muted">
                    <span>CVSS: <strong className="text-cv-danger">{vuln.cvss}</strong></span>
                    <span>EPSS: <strong className="text-cv-blue">{vuln.epss}</strong></span>
                  </div>
                </button>
              ))}
            </div>
          </div>

        </div>

        {/* Level 6: Master Controls & Direct Remediation Action */}
        <div className="p-4 rounded-lg bg-cv-bg border border-cv-border space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-cv-border pb-2 font-mono text-xs">
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-cv-blue" />
              <span className="font-bold text-cv-blue uppercase">
                Level 6: Master Controls Mitigating {currentVuln?.cve} ({currentVuln?.controls?.length || 0} Controls)
              </span>
            </div>
            <span className="text-cv-muted">
              Exploit Status: <strong className="text-cv-danger">{currentVuln?.exploitStatus}</strong>
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono text-xs">
            {currentVuln?.controls?.map((ctrl) => (
              <div
                key={ctrl.id}
                className="p-3.5 rounded-lg bg-white border border-cv-border hover:border-slate-300 space-y-2 shadow-sm"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-0.5 rounded bg-cv-blueLight text-cv-blue border border-blue-200 font-bold">
                      {ctrl.code}
                    </span>
                    <span className="font-bold text-cv-text font-sans">{ctrl.name}</span>
                  </div>
                  <Badge
                    variant={ctrl.status === 'COMPLIANT' ? 'compliant' : ctrl.status === 'IN_PROGRESS' ? 'cyan' : 'partial'}
                    size="xs"
                  >
                    {ctrl.status}
                  </Badge>
                </div>

                <div className="text-[11px] text-cv-muted">
                  <span>Effectiveness: </span>
                  <strong className="text-cv-blue">{ctrl.effectiveness}</strong>
                  <span className="ml-3 text-cv-muted">Frameworks: {ctrl.frameworks}</span>
                </div>

                <div className="p-2 rounded bg-green-50 border border-green-200 text-[11px] text-cv-success font-semibold">
                  <strong>Mandated Remediation:</strong> {ctrl.actionRequired}
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Remediation Backlog & SLA Tracking Table */}
      <div className="cyber-card rounded-lg border-cv-border overflow-hidden space-y-3 p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-cv-border pb-3">
          <div>
            <h3 className="text-sm font-sans font-semibold text-cv-text flex items-center space-x-2">
              <Clock className="w-4 h-4 text-cv-warning" />
              <span>REMEDIATION BACKLOG & REGULATORY SLA STATUS</span>
            </h3>
            <p className="text-xs text-cv-muted">
              RBI, SEBI & Internal P0 Vulnerability SLA countdowns
            </p>
          </div>

          <div className="flex items-center space-x-2 font-mono text-xs">
            <span className="text-cv-muted">Filter:</span>
            <input
              type="text"
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              placeholder="Search CVE or team..."
              className="px-3 py-1.5 bg-cv-bg border border-cv-border rounded-lg text-xs text-cv-text focus:outline-none focus:border-cv-blue"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="border-b border-cv-border text-cv-muted uppercase">
                <th className="pb-3 px-3">Ticket ID & CVE</th>
                <th className="pb-3 px-3">Vulnerability Title</th>
                <th className="pb-3 px-3">Target Asset & Service</th>
                <th className="pb-3 px-3">CVSS / EPSS</th>
                <th className="pb-3 px-3">Financial Risk</th>
                <th className="pb-3 px-3">Assigned Team</th>
                <th className="pb-3 px-3 text-right">SLA Countdown</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-cv-border">
              {data.remediationBacklog
                .filter(item => 
                  item.title.toLowerCase().includes(searchFilter.toLowerCase()) ||
                  item.cve.toLowerCase().includes(searchFilter.toLowerCase()) ||
                  item.assignedTeam.toLowerCase().includes(searchFilter.toLowerCase())
                )
                .map((ticket) => (
                  <tr key={ticket.id} className="hover:bg-cv-bg transition-colors">
                    <td className="py-3 px-3">
                      <div className="font-bold text-cv-text">{ticket.id}</div>
                      <span className="text-cv-blue font-semibold">{ticket.cve}</span>
                    </td>
                    <td className="py-3 px-3">
                      <div className="font-bold text-cv-text font-sans">{ticket.title}</div>
                      <Badge variant="critical" size="xs" className="mt-0.5">
                        {ticket.priority}
                      </Badge>
                    </td>
                    <td className="py-3 px-3 text-cv-muted">
                      <div className="truncate max-w-xs text-cv-text">{ticket.asset}</div>
                      <span className="text-[10px] text-cv-muted">{ticket.businessService}</span>
                    </td>
                    <td className="py-3 px-3 text-cv-text">
                      <div>CVSS: <strong className="text-cv-danger">{ticket.cvss}</strong></div>
                      <span className="text-[10px] text-cv-blue font-semibold">EPSS: {(ticket.epss * 100).toFixed(0)}%</span>
                    </td>
                    <td className="py-3 px-3 font-bold text-cv-text">
                      {ticket.financialExposure}
                    </td>
                    <td className="py-3 px-3 text-cv-muted">
                      {ticket.assignedTeam}
                    </td>
                    <td className="py-3 px-3 text-right">
                      {ticket.slaStatus === 'BREACHED' ? (
                        <span className="inline-flex items-center px-2.5 py-1 rounded bg-red-50 text-cv-danger border border-red-200 font-bold">
                          BREACHED ({Math.abs(ticket.slaDaysRemaining)}d Ago)
                        </span>
                      ) : ticket.slaStatus === 'EXPIRING_SOON' ? (
                        <span className="inline-flex items-center px-2.5 py-1 rounded bg-amber-50 text-cv-warning border border-amber-200 font-bold">
                          {ticket.slaDaysRemaining}d Remaining
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-1 rounded bg-green-50 text-cv-success border border-green-200 font-semibold">
                          {ticket.slaDaysRemaining}d (On Track)
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
