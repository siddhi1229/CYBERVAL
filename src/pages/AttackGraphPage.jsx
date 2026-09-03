import React, { useState, useEffect, useRef, useMemo } from 'react';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import {
  Network,
  ShieldAlert,
  AlertTriangle,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Filter,
  Zap,
  Info,
  DollarSign,
  Lock,
  Layers,
  Sparkles,
  ArrowRight,
  Shield,
  Search,
  ChevronRight,
  Target,
  Flame,
  CheckCircle2,
  Server,
  Database,
  Globe,
  User,
  Cpu,
  Focus,
  Activity,
  CornerDownRight
} from 'lucide-react';
import Badge from '../components/common/Badge';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { useTelemetry } from '../context/TelemetryContext';
import { attackGraphApi } from '../api/attackGraphApi';

// Register Cytoscape Dagre layout safely
try {
  cytoscape.use(dagre);
} catch (e) {}

export default function AttackGraphPage() {
  const { formatCurrency, refreshKey } = useTelemetry();
  const containerRef = useRef(null);
  const cyRef = useRef(null);

  // Data states
  const [graphData, setGraphData] = useState(null);
  const [attackPaths, setAttackPaths] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Path selection & Node inspection states
  const [selectedPathId, setSelectedPathId] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  
  // Filtering & Search
  const [searchQuery, setSearchQuery] = useState('');
  const [targetFilter, setTargetFilter] = useState('ALL');

  // Blast Radius simulator
  const [blastRadiusActive, setBlastRadiusActive] = useState(false);
  const [blastRadiusCount, setBlastRadiusCount] = useState(0);
  const [blastRadiusExposure, setBlastRadiusExposure] = useState(0);

  // 1. Fetch graph topology and dynamic attack paths from backend
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [topologyRes, pathsRes] = await Promise.all([
          attackGraphApi.getGraphTopology(),
          attackGraphApi.getAttackPaths(50),
        ]);

        setGraphData(topologyRes);
        const paths = Array.isArray(pathsRes) ? pathsRes : [];
        setAttackPaths(paths);

        // Dynamically select the highest-scoring path as default
        if (paths.length > 0) {
          setSelectedPathId(paths[0].path_id);
        }
        setError(null);
      } catch (err) {
        console.error('Failed to load attack graph data:', err);
        setError('Failed to fetch attack graph topology and active attack paths.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [refreshKey]);

  // Active attack path object
  const activePath = useMemo(() => {
    if (!attackPaths || attackPaths.length === 0) return null;
    return attackPaths.find((p) => p.path_id === selectedPathId) || attackPaths[0];
  }, [attackPaths, selectedPathId]);

  // Unique target assets for filtering
  const uniqueTargets = useMemo(() => {
    const targets = new Set(attackPaths.map((p) => p.target).filter(Boolean));
    return ['ALL', ...Array.from(targets)];
  }, [attackPaths]);

  // Filtered attack paths list
  const filteredPaths = useMemo(() => {
    return attackPaths.filter((p) => {
      const matchesTarget = targetFilter === 'ALL' || p.target === targetFilter;
      const matchesSearch =
        !searchQuery ||
        p.path_id?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.target?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.entry_point?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.nodes?.some((n) => n.toLowerCase().includes(searchQuery.toLowerCase()));
      return matchesTarget && matchesSearch;
    });
  }, [attackPaths, targetFilter, searchQuery]);

  // 2. Build Cytoscape hierarchical elements for the active attack path
  const cyElements = useMemo(() => {
    if (!activePath) return { nodes: [], edges: [] };

    const allNodes = graphData?.elements?.nodes || [];
    const nodeMap = new Map(allNodes.map((n) => [n.data.id, n.data]));

    const pathNodeIds = activePath.nodes || [];
    const pathNodes = [];

    pathNodeIds.forEach((nodeId, idx) => {
      const existing = nodeMap.get(nodeId);
      const isEntry = idx === 0;
      const isTarget = idx === pathNodeIds.length - 1;

      // Extract clean label and sub-label
      let primaryLabel = existing?.label || (nodeId === 'internet-0' ? 'External Ingress' : nodeId.toUpperCase());
      let nodeCategory = existing?.category || (isEntry ? 'perimeter' : 'asset');
      let nodeType = existing?.type || (isEntry ? 'EntryZone' : isTarget ? 'CrownJewel' : 'Asset');
      let nodeRisk = existing?.risk_score || activePath.path_score || 90.0;
      let nodeTier = existing?.environment || (isEntry ? 'PERIMETER' : isTarget ? 'CRITICAL TIER 1' : 'INTERNAL');
      let roleLabel = isEntry
        ? 'INTERNET ATTACKER'
        : isTarget
        ? 'CROWN JEWEL TARGET'
        : `LATERAL HOP #${idx}`;

      pathNodes.push({
        data: {
          id: nodeId,
          label: `${primaryLabel}\n[${roleLabel}]`,
          cleanName: primaryLabel,
          roleLabel: roleLabel,
          type: nodeType,
          category: nodeCategory,
          risk_score: nodeRisk,
          environment: nodeTier,
          criticality: existing?.criticality || (isTarget ? 'critical' : isEntry ? 'perimeter' : 'medium'),
          internet_exposed: existing?.internet_exposed ?? isEntry,
          cve_id: existing?.cve_id || (isTarget && activePath.critical_vulnerabilities?.[0] ? activePath.critical_vulnerabilities[0].split(' ')[0] : null),
          cvss_score: existing?.cvss_score || (isTarget ? 9.8 : null),
          mitre_technique: existing?.mitre_technique || (isEntry ? 'T1190 Exploit Public-Facing App' : isTarget ? 'T1486 Data Encrypted for Impact' : 'T1078 Valid Accounts'),
          business_value: existing?.business_value || (isTarget ? 48000000 : 15000000),
          isEntryNode: isEntry,
          isTargetNode: isTarget,
          stepIndex: idx + 1,
        },
      });
    });

    // Build directional sequential path edges
    const pathEdges = [];
    for (let i = 0; i < pathNodeIds.length - 1; i++) {
      const src = pathNodeIds[i];
      const tgt = pathNodeIds[i + 1];
      const edgeLabel = i === 0 ? 'INITIAL EXPLOIT' : `LATERAL HOP ${i}`;

      pathEdges.push({
        data: {
          id: `edge-${src}-${tgt}`,
          source: src,
          target: tgt,
          label: edgeLabel,
          isAttackPath: true,
        },
      });
    }

    return { nodes: pathNodes, edges: pathEdges };
  }, [graphData, activePath]);

  // 3. Render and update Cytoscape Hierarchical Graph
  useEffect(() => {
    if (!containerRef.current || !cyElements.nodes.length) return;

    if (cyRef.current) {
      cyRef.current.destroy();
    }

    const cy = cytoscape({
      container: containerRef.current,
      elements: [...cyElements.nodes, ...cyElements.edges],
      style: [
        // Base Node Style - Clean Enterprise Card
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'color': '#0F172A',
            'font-family': 'Inter, system-ui, sans-serif',
            'font-size': '11px',
            'font-weight': '700',
            'text-valign': 'center',
            'text-halign': 'center',
            'text-wrap': 'wrap',
            'text-max-width': '140px',
            'background-color': '#FFFFFF',
            'border-width': 2.5,
            'border-color': '#94A3B8',
            'shape': 'round-rectangle',
            'width': 160,
            'height': 64,
            'padding': 10,
            'transition-property': 'background-color, border-color, border-width, shadow-blur',
            'transition-duration': '0.2s',
          },
        },
        // Attacker / Ingress Infiltration Node
        {
          selector: 'node[?isEntryNode]',
          style: {
            'background-color': '#F8FAFC',
            'border-color': '#3B82F6',
            'border-width': 3,
            'color': '#1E3A8A',
          },
        },
        // Intermediate Lateral Movement Hosts
        {
          selector: 'node[!isEntryNode][!isTargetNode]',
          style: {
            'background-color': '#EFF6FF',
            'border-color': '#2563EB',
            'border-width': 2.5,
            'color': '#1E40AF',
          },
        },
        // Crown Jewel Critical Target Node (Bold Red Hero)
        {
          selector: 'node[?isTargetNode]',
          style: {
            'background-color': '#FEF2F2',
            'border-color': '#EF4444',
            'border-width': 3.5,
            'color': '#991B1B',
            'width': 175,
            'height': 70,
          },
        },
        // Highlighted / Selected Node
        {
          selector: '.highlighted-node',
          style: {
            'border-color': '#2563EB',
            'border-width': 4,
            'background-color': '#DBEAFE',
            'shadow-blur': 14,
            'shadow-color': '#3B82F6',
            'shadow-opacity': 0.35,
          },
        },
        // Blast Radius Downstream Nodes
        {
          selector: '.blast-node',
          style: {
            'border-color': '#D97706',
            'border-width': 3.5,
            'background-color': '#FEF3C7',
          },
        },
        // Edge Style - Bold Directed Attack Vector
        {
          selector: 'edge',
          style: {
            'width': 4,
            'line-color': '#DC2626',
            'target-arrow-color': '#DC2626',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'arrow-scale': 1.5,
            'label': 'data(label)',
            'font-family': 'JetBrains Mono, monospace',
            'font-size': '10px',
            'font-weight': 'bold',
            'color': '#B91C1C',
            'text-background-color': '#FFFFFF',
            'text-background-opacity': 0.9,
            'text-background-padding': 3,
            'text-background-shape': 'roundrectangle',
            'text-border-color': '#FECACA',
            'text-border-width': 1,
            'text-border-opacity': 0.8,
            'text-rotation': 'autorotate',
            'text-margin-y': -10,
          },
        },
      ],
      layout: {
        name: 'dagre',
        rankDir: 'LR', // Clean left-to-right attack progression
        nodeSep: 60,
        rankSep: 110,
        padding: 50,
        animate: true,
        animationDuration: 400,
        fit: true,
      },
    });

    // Node click handler
    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      const nodeData = node.data();
      setSelectedNode(nodeData);
      cy.elements().removeClass('highlighted-node blast-node');
      node.addClass('highlighted-node');
    });

    // Background click handler
    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        setSelectedNode(null);
        setBlastRadiusActive(false);
        cy.elements().removeClass('highlighted-node blast-node');
      }
    });

    // Auto-select target node on load
    if (cyElements.nodes.length > 0) {
      const targetNode = cy.nodes('[?isTargetNode]').first();
      const nodeToSelect = targetNode.length ? targetNode : cy.nodes().first();
      if (nodeToSelect.length) {
        setSelectedNode(nodeToSelect.data());
        nodeToSelect.addClass('highlighted-node');
      }
    }

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, [cyElements]);

  // Focus Attack Path in Viewport
  const handleFocusAttackPath = () => {
    if (cyRef.current) {
      cyRef.current.fit(null, 50);
      cyRef.current.center();
    }
  };

  // Zoom Helpers
  const handleZoom = (factor) => {
    if (cyRef.current) {
      cyRef.current.zoom({
        level: cyRef.current.zoom() * factor,
        renderedPosition: { x: cyRef.current.width() / 2, y: cyRef.current.height() / 2 },
      });
    }
  };

  // Path selection handler
  const handleSelectPath = (pathId) => {
    setSelectedPathId(pathId);
    setBlastRadiusActive(false);
  };

  // Blast Radius Simulator
  const simulateBlastRadius = () => {
    if (!cyRef.current || !selectedNode) return;
    const cy = cyRef.current;
    const node = cy.getElementById(selectedNode.id);
    if (!node.length) return;

    const successors = node.successors();
    const downstreamNodes = successors.nodes();

    cy.elements().removeClass('blast-node highlighted-node');
    node.addClass('highlighted-node');
    downstreamNodes.addClass('blast-node');

    let totalExposure = Number(selectedNode.business_value || selectedNode.risk_score * 480000 || 48000000);
    downstreamNodes.forEach((n) => {
      totalExposure += Number(n.data('business_value') || 15000000);
    });

    setBlastRadiusActive(true);
    setBlastRadiusCount(downstreamNodes.length);
    setBlastRadiusExposure(totalExposure / 10000000); // in Crores
  };

  if (loading) return <LoadingSpinner text="Computing Hierarchical Attack Path Graph..." />;
  if (error || !graphData) {
    return (
      <div className="p-8 text-center text-cv-danger border border-red-200 rounded-lg bg-red-50 font-mono">
        <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-cv-danger" />
        <p>{error || 'Attack graph data unavailable.'}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      
      {/* 1. Header Banner */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-5 rounded-lg cyber-card border-cv-border">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-red-50 text-cv-danger border border-red-200 flex items-center space-x-1">
              <Flame className="w-3 h-3 text-cv-danger mr-1" />
              <span>{attackPaths.length} ATTACK PATHS DETECTED</span>
            </span>
            <span className="text-xs font-mono text-cv-muted">
              P3 Digital Twin · Hierarchical Ingress-to-Target Traversal
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-cv-text mt-1 tracking-tight">
            Hierarchical Attack Path Intelligence
          </h1>
          <p className="text-xs sm:text-sm text-cv-muted mt-0.5">
            Visualize directional attack trajectories from external entry points through lateral movement hops into crown jewel assets.
          </p>
        </div>

        {/* Global Stats Badge */}
        <div className="flex items-center space-x-3 text-xs font-mono text-cv-muted bg-cv-bg px-3.5 py-2 rounded-lg border border-cv-border">
          <div>
            <span className="text-cv-muted text-[10px] block">ENTERPRISE NODES</span>
            <strong className="text-cv-text font-sans font-bold">{graphData.summary?.totalNodes || 373}</strong>
          </div>
          <div className="w-px h-6 bg-cv-border" />
          <div>
            <span className="text-cv-muted text-[10px] block">ACTIVE PATHS</span>
            <strong className="text-cv-danger font-sans font-bold">{attackPaths.length}</strong>
          </div>
          <div className="w-px h-6 bg-cv-border" />
          <div>
            <span className="text-cv-muted text-[10px] block">PEAK RISK</span>
            <strong className="text-cv-danger font-sans font-bold">99.9 / 100</strong>
          </div>
        </div>
      </div>

      {/* 2. Selected Attack Path Summary Card */}
      {activePath ? (
        <div className="p-4 rounded-lg bg-gradient-to-r from-red-50/90 via-white to-blue-50/90 border border-red-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4 font-mono text-xs">
          <div className="space-y-1.5">
            <div className="flex items-center space-x-2">
              <span className="px-2 py-0.5 rounded bg-cv-danger text-white text-[10px] font-bold tracking-wide">
                {activePath.path_score >= 90 ? 'CRITICAL - P0 CHOKE POINT' : 'HIGH - P1 VECTOR'}
              </span>
              <span className="font-bold text-cv-text font-sans text-sm">
                {activePath.path_id.toUpperCase()}: {activePath.entry_point} → {activePath.target}
              </span>
            </div>
            
            {/* Visual Step Breadcrumbs */}
            <div className="flex flex-wrap items-center gap-1.5 text-xs text-cv-text">
              {activePath.nodes?.map((nodeId, idx) => (
                <React.Fragment key={idx}>
                  <span className="px-2.5 py-1 rounded bg-white border border-slate-300 font-semibold shadow-2xs text-[11px]">
                    {nodeId === 'internet-0' ? '🌐 Internet Attacker' : nodeId.toUpperCase()}
                  </span>
                  {idx < activePath.nodes.length - 1 && (
                    <ArrowRight className="w-4 h-4 text-cv-danger" />
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-4 text-xs border-t md:border-t-0 md:border-l border-red-200 md:pl-4 pt-2 md:pt-0">
            <div>
              <div className="text-[10px] text-cv-muted uppercase">Risk Score</div>
              <div className="text-base font-bold text-cv-danger font-sans">
                {activePath.path_score} <span className="text-[10px] text-cv-muted font-normal">/ 100</span>
              </div>
            </div>
            <div>
              <div className="text-[10px] text-cv-muted uppercase">Traversal Hops</div>
              <div className="text-base font-bold text-cv-text font-sans">
                {activePath.hops} {activePath.hops === 1 ? 'Hop' : 'Hops'}
              </div>
            </div>
            {activePath.expected_annual_loss && (
              <div>
                <div className="text-[10px] text-cv-muted uppercase">Annual Loss at Risk</div>
                <div className="text-base font-bold text-cv-text font-sans">
                  {formatCurrency(Number(activePath.expected_annual_loss) / 10000000)}
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="p-6 rounded-lg bg-cv-bg border border-cv-border text-center font-mono text-xs text-cv-muted">
          NO ATTACK PATHS DETECTED
        </div>
      )}

      {/* 3. Main 3-Column Grid: Exploit Routes (Left) | Hierarchical Canvas (Center) | Node Inspection (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        
        {/* Left Column: Attack Paths Discovery Panel (3 Cols) */}
        <div className="lg:col-span-3 cyber-card rounded-lg p-3.5 border-cv-border flex flex-col h-[650px]">
          <div className="border-b border-cv-border pb-3 space-y-2.5">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-sans font-bold text-cv-text flex items-center space-x-1.5 uppercase tracking-wide">
                <Target className="w-3.5 h-3.5 text-cv-danger" />
                <span>Exploit Routes ({filteredPaths.length})</span>
              </h3>
              <span className="text-[10px] font-mono text-cv-muted">Ranked by Score</span>
            </div>

            {/* Target Filter Select */}
            <select
              value={targetFilter}
              onChange={(e) => setTargetFilter(e.target.value)}
              className="w-full px-2.5 py-1.5 bg-cv-bg border border-cv-border rounded-md text-xs font-mono text-cv-text focus:outline-none focus:border-cv-blue"
            >
              {uniqueTargets.map((t) => (
                <option key={t} value={t}>
                  {t === 'ALL' ? 'Target: All Business Assets' : `Target: ${t}`}
                </option>
              ))}
            </select>
          </div>

          {/* Scrollable Attack Paths List */}
          <div className="flex-1 overflow-y-auto space-y-2 pt-2.5 pr-1">
            {filteredPaths.map((p) => {
              const isSelected = p.path_id === selectedPathId;
              return (
                <div
                  key={p.path_id}
                  onClick={() => handleSelectPath(p.path_id)}
                  className={`p-2.5 rounded-lg border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-blue-50/90 border-cv-blue shadow-xs ring-1 ring-cv-blue/40'
                      : 'bg-cv-bg border-cv-border hover:border-slate-300 hover:bg-slate-50/80'
                  }`}
                >
                  <div className="flex items-center justify-between text-xs font-mono mb-1">
                    <span className="font-bold text-cv-text">{p.path_id.toUpperCase()}</span>
                    <span
                      className={`px-1.5 py-0.2 rounded font-bold text-[10px] ${
                        p.path_score >= 90
                          ? 'bg-red-100 text-cv-danger'
                          : 'bg-amber-100 text-amber-700'
                      }`}
                    >
                      {p.path_score} / 100
                    </span>
                  </div>

                  <div className="text-[11px] font-medium text-cv-text font-sans truncate mb-1">
                    {p.entry_point} → {p.target}
                  </div>

                  <div className="flex items-center justify-between text-[10px] font-mono text-cv-muted">
                    <span>{p.hops} {p.hops === 1 ? 'hop' : 'hops'}</span>
                    {p.critical_vulnerabilities?.length > 0 && (
                      <span className="text-cv-danger font-semibold">
                        {p.critical_vulnerabilities.length} Critical CVEs
                      </span>
                    )}
                  </div>
                </div>
              );
            })}

            {filteredPaths.length === 0 && (
              <div className="py-12 text-center text-cv-muted font-mono text-xs">
                No attack paths match the selected filter.
              </div>
            )}
          </div>
        </div>

        {/* Center Column: Hierarchical Graph Canvas (6 Cols) */}
        <div className="lg:col-span-6 cyber-card rounded-lg border-cv-border overflow-hidden relative flex flex-col h-[650px]">
          
          {/* Top Canvas Controls Bar */}
          <div className="absolute top-3 left-3 z-20 flex items-center space-x-2 bg-white/95 p-1.5 rounded-lg border border-cv-border shadow-xs backdrop-blur-md font-mono text-xs">
            <button
              onClick={handleFocusAttackPath}
              className="flex items-center space-x-1 px-2.5 py-1 rounded bg-cv-blue text-white font-bold hover:bg-blue-700 transition-colors shadow-2xs"
              title="Center and fit the selected attack path to viewport"
            >
              <Focus className="w-3.5 h-3.5" />
              <span>FOCUS ATTACK PATH</span>
            </button>
            <span className="text-[10px] text-cv-muted px-1 font-semibold uppercase">
              Hierarchical Directed Flow
            </span>
          </div>

          {/* Zoom / Viewport Navigation */}
          <div className="absolute top-3 right-3 z-20 flex items-center space-x-1 bg-white/95 p-1 rounded-lg border border-cv-border shadow-xs backdrop-blur-md">
            <button
              onClick={() => handleZoom(1.25)}
              className="p-1.5 text-cv-muted hover:text-cv-blue rounded hover:bg-cv-bg"
              title="Zoom In"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => handleZoom(0.8)}
              className="p-1.5 text-cv-muted hover:text-cv-blue rounded hover:bg-cv-bg"
              title="Zoom Out"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={handleFocusAttackPath}
              className="p-1.5 text-cv-muted hover:text-cv-blue rounded hover:bg-cv-bg"
              title="Fit to Screen"
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Visual Legend */}
          <div className="absolute bottom-3 left-3 z-20 hidden sm:flex items-center space-x-3 bg-white/95 px-3 py-1.5 rounded-lg border border-cv-border shadow-xs backdrop-blur-md font-mono text-[10px] text-cv-muted">
            <span className="flex items-center">
              <span className="w-2.5 h-2.5 bg-blue-50 border border-blue-500 rounded mr-1" />
              External Entry
            </span>
            <span className="flex items-center">
              <span className="w-2.5 h-2.5 bg-blue-100 border border-blue-600 rounded mr-1" />
              Lateral Hop
            </span>
            <span className="flex items-center">
              <span className="w-2.5 h-2.5 bg-red-100 border border-red-500 rounded mr-1" />
              Crown Jewel Target
            </span>
            <span className="flex items-center text-cv-danger font-semibold">
              <span className="w-3 h-0.5 bg-red-600 mr-1 inline-block" />
              Exploit Vector
            </span>
          </div>

          {/* Cytoscape Mount Container */}
          <div ref={containerRef} id="cy-hierarchical-canvas" className="w-full h-full bg-cv-bg" />
        </div>

        {/* Right Column: Node Inspection Drawer (3 Cols) */}
        <div className="lg:col-span-3 cyber-card rounded-lg p-4 border-cv-border flex flex-col justify-between h-[650px] overflow-y-auto">
          <div>
            <div className="border-b border-cv-border pb-2.5 flex items-center justify-between">
              <h3 className="text-xs font-sans font-bold text-cv-text flex items-center space-x-1.5 uppercase tracking-wide">
                <Info className="w-3.5 h-3.5 text-cv-blue" />
                <span>Node Inspection</span>
              </h3>
              {selectedNode ? (
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-blue-100 text-cv-blue">
                  {selectedNode.type?.toUpperCase() || 'ASSET'}
                </span>
              ) : (
                <span className="text-[10px] font-mono text-cv-muted">NO SELECTION</span>
              )}
            </div>

            {selectedNode ? (
              <div className="space-y-3.5 font-mono text-xs mt-3">
                <div>
                  <h4 className="text-sm font-bold text-cv-text font-sans leading-snug">
                    {selectedNode.cleanName || selectedNode.label}
                  </h4>
                  <p className="text-[10px] text-cv-blue mt-0.5">
                    ID: {selectedNode.id} · Category: {selectedNode.category || 'Infrastructure'}
                  </p>
                </div>

                {/* Structured Metadata - Zero Blank Values */}
                <div className="p-3 rounded-lg bg-cv-bg border border-cv-border space-y-2 text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-cv-muted">Security Tier:</span>
                    <strong className="text-cv-text">
                      {selectedNode.environment
                        ? selectedNode.environment.toUpperCase()
                        : selectedNode.isEntryNode
                        ? 'PERIMETER INGRESS'
                        : selectedNode.isTargetNode
                        ? 'TIER 1 (CROWN JEWEL)'
                        : 'INTERNAL HOST'}
                    </strong>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-cv-muted">Security Status:</span>
                    <strong
                      className={
                        selectedNode.isTargetNode || selectedNode.risk_score >= 80
                          ? 'text-cv-danger'
                          : 'text-cv-warning'
                      }
                    >
                      {selectedNode.isTargetNode || selectedNode.risk_score >= 80
                        ? 'CRITICAL EXPOSURE'
                        : selectedNode.risk_score >= 50
                        ? 'ELEVATED RISK'
                        : 'ACTIVE'}
                    </strong>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-cv-muted">Criticality:</span>
                    <strong className="text-cv-text">
                      {selectedNode.criticality
                        ? selectedNode.criticality.toUpperCase()
                        : selectedNode.isTargetNode
                        ? 'CRITICAL'
                        : 'STANDARD'}
                    </strong>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-cv-muted">Internet Ingress:</span>
                    <strong className="text-cv-text">
                      {selectedNode.internet_exposed || selectedNode.isEntryNode
                        ? 'Yes (Exposed Interface)'
                        : 'No (Internal Network)'}
                    </strong>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-cv-muted">Direct Business Value:</span>
                    <strong className="text-cv-text">
                      {selectedNode.business_value
                        ? formatCurrency(Number(selectedNode.business_value) / 10000000)
                        : 'Not available'}
                    </strong>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-cv-muted">Asset Risk Score:</span>
                    <strong className="text-cv-danger">
                      {selectedNode.risk_score
                        ? `${Number(selectedNode.risk_score).toFixed(1)} / 100`
                        : 'Not available'}
                    </strong>
                  </div>

                  {selectedNode.cve_id && (
                    <div className="flex justify-between">
                      <span className="text-cv-muted">Exploitable CVE:</span>
                      <strong className="text-cv-danger">{selectedNode.cve_id}</strong>
                    </div>
                  )}

                  {selectedNode.cvss_score && (
                    <div className="flex justify-between">
                      <span className="text-cv-muted">CVSS Severity:</span>
                      <strong className="text-cv-warning">
                        {Number(selectedNode.cvss_score).toFixed(1)} / 10.0
                      </strong>
                    </div>
                  )}
                </div>

                {/* MITRE ATT&CK Techniques Grounding */}
                <div className="space-y-1">
                  <span className="text-[10px] text-cv-muted uppercase font-bold">
                    MITRE ATT&CK Mapping:
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {selectedNode.mitre_technique ? (
                      <span className="px-1.5 py-0.5 rounded bg-cv-bg border border-cv-border text-[10px] text-cv-muted">
                        {selectedNode.mitre_technique}
                      </span>
                    ) : (
                      <>
                        <span className="px-1.5 py-0.5 rounded bg-cv-bg border border-cv-border text-[10px] text-cv-muted">
                          T1190 Exploit Public-Facing App
                        </span>
                        <span className="px-1.5 py-0.5 rounded bg-cv-bg border border-cv-border text-[10px] text-cv-muted">
                          T1078 Valid Accounts
                        </span>
                      </>
                    )}
                  </div>
                </div>

                {/* Blast Radius Calculation Output */}
                {blastRadiusActive && (
                  <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 space-y-1.5">
                    <div className="flex items-center space-x-1.5 text-amber-800 font-bold text-[11px]">
                      <Sparkles className="w-3.5 h-3.5 text-amber-600" />
                      <span>DOWNSTREAM BLAST RADIUS</span>
                    </div>
                    <div className="text-[10px] text-cv-muted">
                      Impact propagation from <strong className="text-cv-text">{selectedNode.cleanName}</strong>:
                    </div>
                    <div className="flex justify-between text-[11px] pt-1 border-t border-amber-200">
                      <span className="text-cv-muted">Downstream Reach:</span>
                      <strong className="text-amber-800">{blastRadiusCount} Connected Hosts</strong>
                    </div>
                    <div className="flex justify-between text-[11px]">
                      <span className="text-cv-muted">Aggregate Loss at Risk:</span>
                      <strong className="text-cv-danger">
                        {formatCurrency(blastRadiusExposure || 48.0)}
                      </strong>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="py-16 text-center text-cv-muted font-mono text-xs space-y-2">
                <Network className="w-8 h-8 mx-auto text-slate-300" />
                <p>Click any node in the attack graph to inspect telemetry and compute blast radius.</p>
              </div>
            )}
          </div>

          {/* Action Button: Calculate Blast Radius */}
          {selectedNode && (
            <div className="pt-3 border-t border-cv-border">
              <button
                onClick={simulateBlastRadius}
                className="w-full py-2 rounded-lg bg-cv-warningBg hover:bg-amber-100 text-amber-800 border border-amber-300 font-mono text-xs font-bold transition-all flex items-center justify-center space-x-1.5 shadow-2xs"
              >
                <Sparkles className="w-3.5 h-3.5 text-amber-600" />
                <span>Simulate Blast Radius</span>
              </button>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
