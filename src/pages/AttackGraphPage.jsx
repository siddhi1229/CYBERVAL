import React, { useState, useEffect, useRef, useMemo } from 'react';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import cola from 'cytoscape-cola';
import {
  Network,
  ShieldAlert,
  AlertTriangle,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Filter,
  Eye,
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
  Cpu
} from 'lucide-react';
import Badge from '../components/common/Badge';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { useTelemetry } from '../context/TelemetryContext';
import { attackGraphApi } from '../api/attackGraphApi';

// Register Cytoscape layout plugins safely
try {
  cytoscape.use(dagre);
} catch (e) {}
try {
  cytoscape.use(cola);
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

  // Progressive Visualization States
  // viewMode: 'path' (Level 2: Path-Only Hero View - DEFAULT) | 'enterprise' (Level 1: Enterprise Overview)
  const [viewMode, setViewMode] = useState('path');
  const [selectedPathId, setSelectedPathId] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [activeLayout, setActiveLayout] = useState('dagre'); // 'dagre' | 'concentric' | 'cola'
  
  // Filtering & Interaction
  const [searchQuery, setSearchQuery] = useState('');
  const [targetFilter, setTargetFilter] = useState('ALL');
  const [blastRadiusActive, setBlastRadiusActive] = useState(false);
  const [blastRadiusCount, setBlastRadiusCount] = useState(0);
  const [blastRadiusExposure, setBlastRadiusExposure] = useState(0);

  // 1. Fetch graph topology and dynamic attack paths
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

  // Currently active attack path object
  const activePath = useMemo(() => {
    if (!attackPaths || attackPaths.length === 0) return null;
    return attackPaths.find((p) => p.path_id === selectedPathId) || attackPaths[0];
  }, [attackPaths, selectedPathId]);

  // Unique targets for filter dropdown
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

  // 2. Compute elements for Cytoscape depending on viewMode
  const cyElements = useMemo(() => {
    if (!graphData || !graphData.elements) return { nodes: [], edges: [] };

    const allNodes = graphData.elements.nodes || [];
    const allEdges = graphData.elements.edges || [];
    const nodeMap = new Map(allNodes.map((n) => [n.data.id, n]));

    if (viewMode === 'path' && activePath) {
      // Level 2: PATH-ONLY VIEW - Render ONLY the nodes and edges belonging to the active attack path
      const pathNodeIds = activePath.nodes || [];
      const pathNodes = [];

      pathNodeIds.forEach((nodeId, idx) => {
        const existingNode = nodeMap.get(nodeId);
        const isEntry = idx === 0;
        const isTarget = idx === pathNodeIds.length - 1;

        if (existingNode) {
          pathNodes.push({
            ...existingNode,
            data: {
              ...existingNode.data,
              isEntryNode: isEntry,
              isTargetNode: isTarget,
              pathSequenceIndex: idx + 1,
            },
          });
        } else {
          // Synthesize node if not in base topology
          pathNodes.push({
            data: {
              id: nodeId,
              label: nodeId.toUpperCase(),
              type: isEntry ? 'EntryZone' : isTarget ? 'CrownJewel' : 'Asset',
              category: isEntry ? 'perimeter' : 'asset',
              risk_score: activePath.path_score || 90.0,
              isEntryNode: isEntry,
              isTargetNode: isTarget,
              pathSequenceIndex: idx + 1,
            },
          });
        }
      });

      // Construct direct sequential path edges
      const pathEdges = [];
      for (let i = 0; i < pathNodeIds.length - 1; i++) {
        const src = pathNodeIds[i];
        const tgt = pathNodeIds[i + 1];
        pathEdges.push({
          data: {
            id: `path-edge-${src}-${tgt}`,
            source: src,
            target: tgt,
            label: i === 0 ? 'EXPLOIT_INGRESS' : 'LATERAL_HOP',
            isAttackPath: true,
          },
        });
      }

      return { nodes: pathNodes, edges: pathEdges };
    }

    // Level 1: ENTERPRISE OVERVIEW - Render full graph with clean visual hierarchy
    return {
      nodes: allNodes.map((n) => {
        const inActivePath = activePath?.nodes?.includes(n.data.id);
        return {
          ...n,
          data: {
            ...n.data,
            inActivePath: !!inActivePath,
          },
        };
      }),
      edges: allEdges.map((e) => {
        const isPathEdge =
          activePath?.nodes &&
          activePath.nodes.includes(e.data.source) &&
          activePath.nodes.includes(e.data.target);
        return {
          ...e,
          data: {
            ...e.data,
            isAttackPath: isPathEdge,
          },
        };
      }),
    };
  }, [graphData, viewMode, activePath]);

  // 3. Initialize and Update Cytoscape Graph
  useEffect(() => {
    if (!containerRef.current || !cyElements.nodes.length) return;

    if (cyRef.current) {
      cyRef.current.destroy();
    }

    const cy = cytoscape({
      container: containerRef.current,
      elements: [...cyElements.nodes, ...cyElements.edges],
      style: [
        // Base Node Style
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'color': '#0F172A',
            'font-family': 'Inter, system-ui, sans-serif',
            'font-size': viewMode === 'path' ? '12px' : '10px',
            'font-weight': '600',
            'text-valign': 'bottom',
            'text-margin-y': 8,
            'text-wrap': 'wrap',
            'text-max-width': '120px',
            'background-color': '#E2E8F0',
            'border-width': 2,
            'border-color': '#94A3B8',
            'width': viewMode === 'path' ? 56 : 36,
            'height': viewMode === 'path' ? 56 : 36,
            'transition-property': 'background-color, border-color, border-width, transform, opacity',
            'transition-duration': '0.25s',
          },
        },
        // Ingress / Perimeter Entry Zone Nodes
        {
          selector: 'node[type="EntryZone"], node[category="perimeter"], node[?isEntryNode]',
          style: {
            'background-color': '#EEF2F6',
            'border-color': '#3B82F6',
            'border-width': 3,
            'shape': 'round-rectangle',
            'width': viewMode === 'path' ? 64 : 44,
            'height': viewMode === 'path' ? 64 : 44,
          },
        },
        // Vulnerable Gateway / DMZ Servers
        {
          selector: 'node[category="server"], node[type="Asset"]',
          style: {
            'background-color': '#EFF6FF',
            'border-color': '#2563EB',
            'border-width': 2.5,
            'shape': 'round-rectangle',
          },
        },
        // Target / Crown Jewel Assets
        {
          selector: 'node[criticality="critical"], node[?isTargetNode]',
          style: {
            'background-color': '#FEF2F2',
            'border-color': '#EF4444',
            'border-width': 4,
            'shape': 'round-rectangle',
            'width': viewMode === 'path' ? 68 : 48,
            'height': viewMode === 'path' ? 68 : 48,
          },
        },
        // Users / Identities
        {
          selector: 'node[type="User"], node[category="identity"]',
          style: {
            'background-color': '#FAF5FF',
            'border-color': '#9333EA',
            'border-width': 2.5,
            'shape': 'ellipse',
          },
        },
        // Business Services
        {
          selector: 'node[type="BusinessService"], node[category="business_service"]',
          style: {
            'background-color': '#F0FDF4',
            'border-color': '#16A34A',
            'border-width': 3,
            'shape': 'hexagon',
            'width': 50,
            'height': 50,
          },
        },
        // Telemetry Findings (SIEM/EDR/CSPM in Enterprise view)
        {
          selector: 'node[category="telemetry"]',
          style: {
            'width': 18,
            'height': 18,
            'font-size': '8px',
            'background-color': '#F8FAFC',
            'border-color': '#CBD5E1',
            'border-width': 1,
            'opacity': 0.6,
          },
        },
        // Base Edge Style
        {
          selector: 'edge',
          style: {
            'width': viewMode === 'path' ? 3.5 : 1.5,
            'line-color': '#94A3B8',
            'target-arrow-color': '#94A3B8',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'arrow-scale': viewMode === 'path' ? 1.4 : 1.0,
            'label': viewMode === 'path' ? 'data(label)' : '',
            'font-family': 'JetBrains Mono, monospace',
            'font-size': '9px',
            'color': '#64748B',
            'text-rotation': 'autorotate',
            'text-margin-y': -8,
            'opacity': viewMode === 'path' ? 1.0 : 0.35,
          },
        },
        // Active Attack Path Edge Style
        {
          selector: 'edge[?isAttackPath]',
          style: {
            'line-color': '#DC2626',
            'target-arrow-color': '#DC2626',
            'width': 4.5,
            'line-style': 'solid',
            'opacity': 1.0,
            'arrow-scale': 1.6,
            'color': '#DC2626',
            'font-weight': 'bold',
          },
        },
        // Highlighted Selected Node
        {
          selector: '.highlighted-node',
          style: {
            'border-color': '#2563EB',
            'border-width': 5,
            'background-color': '#DBEAFE',
            'shadow-blur': 15,
            'shadow-color': '#3B82F6',
            'shadow-opacity': 0.4,
          },
        },
        // Downstream Blast Radius Nodes
        {
          selector: '.blast-node',
          style: {
            'border-color': '#D97706',
            'border-width': 4,
            'background-color': '#FEF3C7',
          },
        },
        // Dimmed Elements
        {
          selector: '.dimmed',
          style: {
            'opacity': 0.15,
          },
        },
      ],
      layout: getLayoutConfig(activeLayout, viewMode),
    });

    // Node click handler
    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      const nodeData = node.data();
      setSelectedNode(nodeData);
      cy.elements().removeClass('highlighted-node blast-node');
      node.addClass('highlighted-node');
    });

    // Background click handler to clear selection
    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        setSelectedNode(null);
        setBlastRadiusActive(false);
        cy.elements().removeClass('highlighted-node blast-node dimmed');
      }
    });

    // Set initial node selection if in path view
    if (viewMode === 'path' && cyElements.nodes.length > 0) {
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
  }, [cyElements, activeLayout, viewMode]);

  // Layout Configuration Generator
  function getLayoutConfig(layoutName, mode) {
    if (layoutName === 'dagre') {
      return {
        name: 'dagre',
        rankDir: mode === 'path' ? 'LR' : 'TB',
        nodeSep: mode === 'path' ? 60 : 35,
        rankSep: mode === 'path' ? 100 : 55,
        animate: true,
        animationDuration: 400,
        padding: 50,
      };
    }
    if (layoutName === 'concentric') {
      return {
        name: 'concentric',
        concentric: (node) => {
          if (node.data('isEntryNode') || node.data('type') === 'EntryZone') return 4;
          if (node.data('category') === 'perimeter') return 3;
          if (node.data('type') === 'Asset') return 2;
          if (node.data('isTargetNode') || node.data('criticality') === 'critical') return 1;
          return 2;
        },
        levelWidth: () => 1,
        padding: 50,
        animate: true,
      };
    }
    if (layoutName === 'cola') {
      return {
        name: 'cola',
        maxSimulationTime: 1200,
        fit: true,
        padding: 40,
        nodeSpacing: () => (mode === 'path' ? 50 : 25),
      };
    }
    return { name: 'breadthfirst', directed: true, padding: 40 };
  }

  // Layout Switcher
  const changeLayout = (layoutName) => {
    setActiveLayout(layoutName);
    if (cyRef.current) {
      const layout = cyRef.current.layout(getLayoutConfig(layoutName, viewMode));
      layout.run();
    }
  };

  // View Mode Switcher (Path View vs Enterprise Overview)
  const handleViewModeChange = (mode) => {
    setViewMode(mode);
    setBlastRadiusActive(false);
    setSelectedNode(null);
  };

  // Path Selection Handler
  const handleSelectPath = (pathId) => {
    setSelectedPathId(pathId);
    setBlastRadiusActive(false);
    if (viewMode !== 'path') {
      setViewMode('path');
    }
  };

  // Blast Radius Simulator
  const simulateBlastRadius = () => {
    if (!cyRef.current || !selectedNode) return;
    const cy = cyRef.current;
    const node = cy.getElementById(selectedNode.id);
    if (!node.length) return;

    const successors = node.successors();
    const downstreamNodes = successors.nodes();

    cy.elements().removeClass('dimmed blast-node highlighted-node');
    cy.elements().addClass('dimmed');
    node.removeClass('dimmed').addClass('highlighted-node');
    successors.removeClass('dimmed');
    downstreamNodes.addClass('blast-node');

    let totalExposure = Number(selectedNode.business_value || selectedNode.risk_score * 480000 || 48000000);
    downstreamNodes.forEach((n) => {
      totalExposure += Number(n.data('business_value') || 15000000);
    });

    setBlastRadiusActive(true);
    setBlastRadiusCount(downstreamNodes.length);
    setBlastRadiusExposure(totalExposure / 10000000); // in Crores
  };

  // Zoom / Navigation Helpers
  const handleZoom = (factor) => {
    if (cyRef.current) {
      cyRef.current.zoom({
        level: cyRef.current.zoom() * factor,
        renderedPosition: { x: cyRef.current.width() / 2, y: cyRef.current.height() / 2 },
      });
    }
  };

  const handleFit = () => {
    if (cyRef.current) cyRef.current.fit(null, 50);
  };

  if (loading) return <LoadingSpinner text="Analyzing Attack Surface & Traversal Paths..." />;
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
      {/* 1. Header Banner with Progressive View Mode Switcher */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-5 rounded-lg cyber-card border-cv-border">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-red-50 text-cv-danger border border-red-200 flex items-center space-x-1">
              <Flame className="w-3 h-3 text-cv-danger mr-1" />
              <span>{attackPaths.length} ATTACK PATHS DETECTED</span>
            </span>
            <span className="text-xs font-mono text-cv-muted">
              P3 Digital Twin · Real-time Graph Traversal
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-cv-text mt-1 tracking-tight">
            Attack Path Intelligence & Exploitation Chains
          </h1>
          <p className="text-xs sm:text-sm text-cv-muted mt-0.5">
            Identify how external adversaries infiltrate ingress zones, escalate privileges, and reach critical financial assets.
          </p>
        </div>

        {/* View Mode Switcher: Level 2 (Path View) vs Level 1 (Enterprise Overview) */}
        <div className="flex items-center space-x-2 bg-cv-bg p-1.5 rounded-lg border border-cv-border font-mono text-xs">
          <button
            onClick={() => handleViewModeChange('path')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md transition-all font-bold ${
              viewMode === 'path'
                ? 'bg-cv-blue text-white shadow-sm'
                : 'text-cv-muted hover:text-cv-text'
            }`}
            title="Focus exclusively on the selected attack path traversal chain"
          >
            <Zap className="w-3.5 h-3.5" />
            <span>Attack Paths (Hero View)</span>
          </button>
          <button
            onClick={() => handleViewModeChange('enterprise')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md transition-all font-bold ${
              viewMode === 'enterprise'
                ? 'bg-cv-blue text-white shadow-sm'
                : 'text-cv-muted hover:text-cv-text'
            }`}
            title="View the complete 373-node enterprise topology"
          >
            <Globe className="w-3.5 h-3.5" />
            <span>Enterprise Overview ({graphData.summary?.totalNodes || 373})</span>
          </button>
        </div>
      </div>

      {/* 2. Hero Selected Attack Path Summary Card */}
      {activePath && (
        <div className="p-4 rounded-lg bg-gradient-to-r from-red-50/80 via-white to-blue-50/80 border border-red-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4 font-mono text-xs">
          <div className="space-y-1.5">
            <div className="flex items-center space-x-2">
              <span className="px-2 py-0.5 rounded bg-cv-danger text-white text-[10px] font-bold">
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
                  <span className="px-2 py-0.5 rounded bg-white border border-slate-300 font-semibold shadow-2xs">
                    {nodeId === 'internet-0' ? '🌐 Internet Ingress' : nodeId.toUpperCase()}
                  </span>
                  {idx < activePath.nodes.length - 1 && (
                    <ArrowRight className="w-3.5 h-3.5 text-cv-danger" />
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
      )}

      {/* 3. Main 3-Column Layout: Paths List (Left) | Canvas (Center) | Node Inspection (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        
        {/* Left Column: Attack Paths Discovery Panel (3 Cols) */}
        <div className="lg:col-span-3 cyber-card rounded-lg p-3 border-cv-border flex flex-col h-[650px]">
          <div className="border-b border-cv-border pb-2.5 space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-sans font-bold text-cv-text flex items-center space-x-1.5 uppercase tracking-wide">
                <Target className="w-3.5 h-3.5 text-cv-danger" />
                <span>Exploit Routes ({filteredPaths.length})</span>
              </h3>
              <span className="text-[10px] font-mono text-cv-muted">Sorted by Score</span>
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

          {/* Scrollable Paths List */}
          <div className="flex-1 overflow-y-auto space-y-2 pt-2 pr-1">
            {filteredPaths.map((p) => {
              const isSelected = p.path_id === selectedPathId;
              return (
                <div
                  key={p.path_id}
                  onClick={() => handleSelectPath(p.path_id)}
                  className={`p-2.5 rounded-lg border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-blue-50/80 border-cv-blue shadow-xs ring-1 ring-cv-blue/30'
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

        {/* Center Column: Cytoscape Visual Canvas (6 Cols) */}
        <div className="lg:col-span-6 cyber-card rounded-lg border-cv-border overflow-hidden relative flex flex-col h-[650px]">
          
          {/* Floating Canvas Toolbar */}
          <div className="absolute top-3 left-3 z-20 flex flex-wrap items-center gap-1.5 bg-white/95 p-1.5 rounded-lg border border-cv-border shadow-xs backdrop-blur-md font-mono text-xs">
            <span className="text-cv-muted px-1.5 text-[10px] uppercase font-bold">Layout:</span>
            <button
              onClick={() => changeLayout('dagre')}
              className={`px-2 py-1 rounded transition-colors ${
                activeLayout === 'dagre'
                  ? 'bg-cv-blue text-white font-bold'
                  : 'text-cv-muted hover:text-cv-text'
              }`}
              title="Hierarchical directed attack progression (Recommended)"
            >
              Hierarchical
            </button>
            <button
              onClick={() => changeLayout('concentric')}
              className={`px-2 py-1 rounded transition-colors ${
                activeLayout === 'concentric'
                  ? 'bg-cv-blue text-white font-bold'
                  : 'text-cv-muted hover:text-cv-text'
              }`}
              title="Concentric security tier arrangement"
            >
              Concentric Tiers
            </button>
            <button
              onClick={() => changeLayout('cola')}
              className={`px-2 py-1 rounded transition-colors ${
                activeLayout === 'cola'
                  ? 'bg-cv-blue text-white font-bold'
                  : 'text-cv-muted hover:text-cv-text'
              }`}
              title="Physics force-directed clustering"
            >
              Physics (Cola)
            </button>
          </div>

          {/* Zoom / Viewport Controls */}
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
              onClick={handleFit}
              className="p-1.5 text-cv-muted hover:text-cv-blue rounded hover:bg-cv-bg"
              title="Fit Viewport"
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Visual Legend */}
          <div className="absolute bottom-3 left-3 z-20 hidden sm:flex items-center space-x-3 bg-white/95 px-3 py-1.5 rounded-lg border border-cv-border shadow-xs backdrop-blur-md font-mono text-[10px] text-cv-muted">
            <span className="flex items-center">
              <span className="w-2.5 h-2.5 bg-blue-100 border border-blue-500 rounded mr-1" />
              Internet Ingress
            </span>
            <span className="flex items-center">
              <span className="w-2.5 h-2.5 bg-blue-50 border border-blue-600 rounded mr-1" />
              Intermediate Host
            </span>
            <span className="flex items-center">
              <span className="w-2.5 h-2.5 bg-red-100 border border-red-500 rounded mr-1" />
              Crown Jewel Target
            </span>
            <span className="flex items-center">
              <span className="w-2.5 h-2.5 bg-purple-100 border border-purple-600 rounded-full mr-1" />
              Compromised User
            </span>
          </div>

          {/* Cytoscape DOM Mount */}
          <div ref={containerRef} id="cy-canvas" className="w-full h-full bg-cv-bg" />
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
                    {selectedNode.label || selectedNode.id}
                  </h4>
                  <p className="text-[10px] text-cv-blue mt-0.5">
                    ID: {selectedNode.id} · Type: {selectedNode.type || 'Asset'}
                  </p>
                </div>

                {/* Structured Metadata Table - Zero Blank Values */}
                <div className="p-3 rounded-lg bg-cv-bg border border-cv-border space-y-2 text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-cv-muted">Security Tier:</span>
                    <strong className="text-cv-text">
                      {selectedNode.environment
                        ? selectedNode.environment.toUpperCase()
                        : selectedNode.isEntryNode || selectedNode.type === 'EntryZone'
                        ? 'PERIMETER INGRESS'
                        : selectedNode.isTargetNode || selectedNode.criticality === 'critical'
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
                      {selectedNode.status ||
                        (selectedNode.risk_score >= 80
                          ? 'CRITICAL EXPOSURE'
                          : selectedNode.risk_score >= 50
                          ? 'ELEVATED RISK'
                          : 'ACTIVE')}
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
                    <span className="text-cv-muted">Asset Risk Score:</span>
                    <strong className="text-cv-danger">
                      {selectedNode.risk_score
                        ? `${Number(selectedNode.risk_score).toFixed(1)} / 100`
                        : 'Not available'}
                    </strong>
                  </div>

                  {selectedNode.cve_id && (
                    <div className="flex justify-between">
                      <span className="text-cv-muted">Known Vulnerability:</span>
                      <strong className="text-cv-danger">{selectedNode.cve_id}</strong>
                    </div>
                  )}

                  {selectedNode.cvss_score && (
                    <div className="flex justify-between">
                      <span className="text-cv-muted">CVSS Score:</span>
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
                    ) : selectedNode.isEntryNode ? (
                      <span className="px-1.5 py-0.5 rounded bg-cv-bg border border-cv-border text-[10px] text-cv-muted">
                        T1190 Exploit Public-Facing App
                      </span>
                    ) : (
                      <>
                        <span className="px-1.5 py-0.5 rounded bg-cv-bg border border-cv-border text-[10px] text-cv-muted">
                          T1078 Valid Accounts
                        </span>
                        <span className="px-1.5 py-0.5 rounded bg-cv-bg border border-cv-border text-[10px] text-cv-muted">
                          T1021 Lateral Movement
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
                      Compromise impact from <strong className="text-cv-text">{selectedNode.label}</strong>:
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
