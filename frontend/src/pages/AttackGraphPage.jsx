import React, { useState, useEffect, useRef } from 'react';
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
  Zap,
  Info,
  DollarSign,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Radio,
  Server
} from 'lucide-react';
import Badge from '../components/common/Badge';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { useTelemetry } from '../context/TelemetryContext';
import { attackGraphApi } from '../api/attackGraphApi';
import { NO_DATA } from '../utils/formatters';

try {
  cytoscape.use(dagre);
  cytoscape.use(cola);
} catch (e) {}

export default function AttackGraphPage() {
  const { formatCurrency, refreshKey } = useTelemetry();
  const containerRef = useRef(null);
  const cyRef = useRef(null);

  const [graphData, setGraphData] = useState(null);
  const [attackPaths, setAttackPaths] = useState([]);
  const [selectedPathIndex, setSelectedPathIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [selectedNode, setSelectedNode] = useState(null);
  const [activeLayout, setActiveLayout] = useState('breadthfirst');
  const [blastRadiusData, setBlastRadiusData] = useState(null);
  const [loadingBlastRadius, setLoadingBlastRadius] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [graphRes, pathsRes] = await Promise.all([
          attackGraphApi.getGraphTopology(),
          attackGraphApi.getAttackPaths({ limit: 20 }),
        ]);
        setGraphData(graphRes);
        setAttackPaths(pathsRes || []);
        setError(null);
      } catch (err) {
        console.error('Failed to load attack graph data:', err);
        setError('Failed to fetch digital twin topology from backend.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [refreshKey]);

  useEffect(() => {
    if (!graphData || !containerRef.current) return;

    // Normalizing elements: backend provides { nodes: [...], edges: [...] }
    const nodes = graphData.nodes || [];
    const edges = graphData.edges || [];

    const cy = cytoscape({
      container: containerRef.current,
      elements: {
        nodes: nodes.map((n) => ({
          data: {
            ...n.data,
            label: n.data.label || n.data.id,
          },
        })),
        edges: edges.map((e) => ({
          data: {
            ...e.data,
            label: e.data.label || e.data.relationship,
          },
        })),
      },
      style: [
        {
          selector: 'node',
          style: {
            label: 'data(label)',
            color: '#17212B',
            'font-family': 'Inter, sans-serif',
            'font-size': '10px',
            'font-weight': 'bold',
            'text-valign': 'bottom',
            'text-margin-y': 5,
            'background-color': '#E2E8F0',
            'border-width': 2,
            'border-color': '#94A3B8',
            width: 42,
            height: 42,
          },
        },
        {
          selector: 'node[type="Asset"]',
          style: {
            'background-color': '#DBEAFE',
            'border-color': '#2563EB',
            shape: 'round-rectangle',
            width: 46,
            height: 46,
          },
        },
        {
          selector: 'node[criticality="critical"]',
          style: {
            'background-color': '#FEE2E2',
            'border-color': '#DC2626',
            'border-width': 3,
          },
        },
        {
          selector: 'node[type="User"]',
          style: {
            'background-color': '#EDE9FE',
            'border-color': '#7C3AED',
            shape: 'ellipse',
            width: 42,
            height: 42,
          },
        },
        {
          selector: 'node[type="Vulnerability"]',
          style: {
            'background-color': '#FEF3C7',
            'border-color': '#D97706',
            shape: 'diamond',
            width: 44,
            height: 44,
          },
        },
        {
          selector: 'node[type="Control"]',
          style: {
            'background-color': '#DCFCE7',
            'border-color': '#16A34A',
            shape: 'hexagon',
            width: 44,
            height: 44,
          },
        },
        {
          selector: 'node[type="BusinessService"]',
          style: {
            'background-color': '#CFFAFE',
            'border-color': '#0891B2',
            shape: 'barrel',
            width: 48,
            height: 48,
          },
        },
        {
          selector: 'node[type="SecurityEvent"], node[type="EDREvent"], node[type="CSPMFinding"]',
          style: {
            'background-color': '#FEE2E2',
            'border-color': '#DC2626',
            shape: 'triangle',
            width: 38,
            height: 38,
          },
        },
        {
          selector: 'edge',
          style: {
            width: 1.5,
            'line-color': '#CBD5E1',
            'target-arrow-color': '#CBD5E1',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'arrow-scale': 1.1,
            label: 'data(relationship)',
            'font-family': 'JetBrains Mono, monospace',
            'font-size': '7px',
            color: '#64748B',
            'text-rotation': 'autorotate',
            'text-margin-y': -6,
          },
        },
        {
          selector: '.highlighted-path-edge',
          style: {
            'line-color': '#DC2626',
            'target-arrow-color': '#DC2626',
            width: 3.5,
            'line-style': 'dashed',
            color: '#EF4444',
          },
        },
        {
          selector: '.highlighted-node',
          style: {
            'border-color': '#DC2626',
            'border-width': 4,
            'background-color': '#FEE2E2',
          },
        },
        {
          selector: '.blast-node',
          style: {
            'border-color': '#D97706',
            'border-width': 3,
            'background-color': '#FEF3C7',
          },
        },
        {
          selector: '.dimmed',
          style: {
            opacity: 0.2,
          },
        },
      ],
      layout: getLayoutConfig(activeLayout),
    });

    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      const nodeData = node.data();
      setSelectedNode(nodeData);
      setBlastRadiusData(null);
      cy.elements().removeClass('highlighted-node dimmed blast-node');
      node.addClass('highlighted-node');
    });

    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        setSelectedNode(null);
        setBlastRadiusData(null);
        cy.elements().removeClass('highlighted-node dimmed blast-node highlighted-path-edge');
      }
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, [graphData]);

  const changeLayout = (layoutName) => {
    setActiveLayout(layoutName);
    if (cyRef.current) {
      const layout = cyRef.current.layout(getLayoutConfig(layoutName));
      layout.run();
    }
  };

  function getLayoutConfig(name) {
    if (name === 'breadthfirst') {
      return {
        name: 'breadthfirst',
        directed: true,
        padding: 40,
        spacingFactor: 1.3,
        animate: true,
        animationDuration: 400,
      };
    }
    if (name === 'cola') {
      return { name: 'cola', maxSimulationTime: 1200, fit: true, padding: 40 };
    }
    return { name: 'cose', animate: true, padding: 40 };
  }

  // Highlight specific attack path returned by backend
  const highlightAttackPath = (path) => {
    if (!cyRef.current || !path) return;
    const cy = cyRef.current;
    cy.elements().removeClass('dimmed highlighted-node blast-node highlighted-path-edge');

    const nodeIds = path.nodes || [];
    cy.elements().addClass('dimmed');

    nodeIds.forEach((nid) => {
      const el = cy.getElementById(nid);
      if (el.length) {
        el.removeClass('dimmed').addClass('highlighted-node');
      }
    });

    // Highlight edges between consecutive path nodes
    for (let i = 0; i < nodeIds.length - 1; i++) {
      const s = nodeIds[i];
      const t = nodeIds[i + 1];
      const edge = cy.edges(`[source="${s}"][target="${t}"]`);
      if (edge.length) {
        edge.removeClass('dimmed').addClass('highlighted-path-edge');
      }
    }
  };

  // Blast radius calculation via backend endpoint
  const calculateBlastRadius = async () => {
    if (!selectedNode || !cyRef.current) return;
    const dbId = selectedNode.db_id;
    if (!dbId) return;

    try {
      setLoadingBlastRadius(true);
      const deps = await attackGraphApi.getAssetDependencies(dbId);
      setBlastRadiusData(deps);

      const cy = cyRef.current;
      cy.elements().removeClass('dimmed blast-node highlighted-node');
      cy.elements().addClass('dimmed');

      const primary = cy.getElementById(selectedNode.id);
      if (primary.length) primary.removeClass('dimmed').addClass('highlighted-node');

      const downstream = deps.downstream_dependencies || [];
      const connected = deps.connected_assets || [];

      [...downstream, ...connected].forEach((d) => {
        const dId = d.id || `asset-${d.id}`;
        const targetNode = cy.getElementById(dId);
        if (targetNode.length) {
          targetNode.removeClass('dimmed').addClass('blast-node');
        }
      });
    } catch (err) {
      console.error('Failed to calculate blast radius:', err);
    } finally {
      setLoadingBlastRadius(false);
    }
  };

  const currentPath = attackPaths[selectedPathIndex] || null;

  if (loading) return <LoadingSpinner text="Rendering live Cytoscape digital twin topology..." />;
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
      
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-lg cyber-card border-cv-border">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-red-50 text-cv-danger border border-red-200">
              CYTOSCAPE.JS DIGITAL TWIN
            </span>
            <span className="text-xs font-mono text-cv-muted">
              {graphData.summary?.total_nodes || 0} Nodes • {graphData.summary?.total_edges || 0} Edges
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-cv-text mt-1 tracking-tight">
            Interactive Cyber Attack Graph & Blast Radius
          </h1>
          <p className="text-xs sm:text-sm text-cv-muted mt-0.5">
            Network reachability, Crown Jewel lateral movement, and multi-source telemetry convergence.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {currentPath && (
            <button
              onClick={() => highlightAttackPath(currentPath)}
              className="flex items-center space-x-2 px-3.5 py-2 rounded-lg bg-cv-dangerBg border border-red-300 text-cv-danger hover:bg-red-100 font-mono text-xs font-semibold transition-all"
            >
              <Zap className="w-4 h-4" />
              <span>HIGHLIGHT ACTIVE KILLCHAIN</span>
            </button>
          )}

          {selectedNode && selectedNode.db_id && (
            <button
              onClick={calculateBlastRadius}
              disabled={loadingBlastRadius}
              className="flex items-center space-x-2 px-3.5 py-2 rounded-lg bg-cv-warningBg border border-amber-300 text-cv-warning hover:bg-amber-100 font-mono text-xs font-semibold transition-all disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              <span>{loadingBlastRadius ? 'CALCULATING...' : 'CALCULATE BLAST RADIUS'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Discovered Attack Path Selector Banner */}
      <div className="p-4 rounded-lg bg-cv-bg border border-cv-border flex flex-col md:flex-row md:items-center justify-between gap-3 font-mono text-xs">
        <div className="flex items-center space-x-3">
          <ShieldAlert className="w-5 h-5 text-cv-danger flex-shrink-0" />
          <div>
            <span className="text-cv-danger font-bold">DISCOVERED ATTACK PATH: </span>
            <select
              value={selectedPathIndex}
              onChange={(e) => {
                const idx = Number(e.target.value);
                setSelectedPathIndex(idx);
                highlightAttackPath(attackPaths[idx]);
              }}
              className="ml-2 bg-white border border-cv-border rounded px-2 py-1 text-cv-text font-bold"
            >
              {attackPaths.map((p, i) => (
                <option key={p.path_id || i} value={i}>
                  Path #{i + 1}: {p.entry_point} → {p.target} (Score: {p.path_score?.toFixed(1) || 'N/A'})
                </option>
              ))}
              {attackPaths.length === 0 && <option>{NO_DATA}</option>}
            </select>
          </div>
        </div>

        {currentPath && (
          <div className="flex items-center space-x-4 text-[11px] text-cv-muted">
            <span>Hops: <strong className="text-cv-text">{currentPath.hops}</strong></span>
            <span>Path Score: <strong className="text-cv-danger">{currentPath.path_score?.toFixed(1) || NO_DATA} / 100</strong></span>
            <span>Critical Assets: <strong className="text-cv-warning">{currentPath.critical_assets?.join(', ') || 'None'}</strong></span>
          </div>
        )}
      </div>

      {/* Main Canvas & Inspection Drawer */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        
        {/* Cytoscape Canvas */}
        <div className="lg:col-span-3 cyber-card rounded-lg border-cv-border overflow-hidden relative flex flex-col h-[620px]">
          
          {/* Layout Controls */}
          <div className="absolute top-3 left-3 z-20 flex flex-wrap items-center gap-2 bg-white/95 p-1.5 rounded-lg border border-cv-border shadow-card backdrop-blur-md font-mono text-xs">
            <span className="text-cv-muted px-2 text-[10px] uppercase font-bold">Layout:</span>
            <button
              onClick={() => changeLayout('breadthfirst')}
              className={`px-2.5 py-1 rounded-lg transition-colors ${activeLayout === 'breadthfirst' ? 'bg-cv-blue text-white font-bold' : 'text-cv-muted hover:text-cv-text'}`}
            >
              Hierarchical
            </button>
            <button
              onClick={() => changeLayout('cola')}
              className={`px-2.5 py-1 rounded-lg transition-colors ${activeLayout === 'cola' ? 'bg-cv-blue text-white font-bold' : 'text-cv-muted hover:text-cv-text'}`}
            >
              Physics (Cola)
            </button>
            <button
              onClick={() => changeLayout('cose')}
              className={`px-2.5 py-1 rounded-lg transition-colors ${activeLayout === 'cose' ? 'bg-cv-blue text-white font-bold' : 'text-cv-muted hover:text-cv-text'}`}
            >
              CoSE Force
            </button>
          </div>

          {/* Canvas Legend */}
          <div className="absolute bottom-3 left-3 z-20 hidden sm:flex items-center space-x-3 bg-white/95 px-3 py-2 rounded-lg border border-cv-border shadow-card backdrop-blur-md font-mono text-[10px] text-cv-muted">
            <span className="flex items-center"><span className="w-2.5 h-2.5 bg-blue-500 rounded mr-1" />Asset</span>
            <span className="flex items-center"><span className="w-2.5 h-2.5 bg-purple-500 rounded-full mr-1" />User</span>
            <span className="flex items-center"><span className="w-2.5 h-2.5 bg-amber-500 rotate-45 mr-1" />Vulnerability</span>
            <span className="flex items-center"><span className="w-2.5 h-2.5 bg-green-500 rounded mr-1" />Control</span>
            <span className="flex items-center"><span className="w-2.5 h-2.5 bg-cyan-500 rounded mr-1" />Service</span>
            <span className="flex items-center"><span className="w-2.5 h-2.5 bg-red-600 rounded mr-1" />Alert</span>
          </div>

          {/* Cytoscape Container */}
          <div ref={containerRef} id="cy-container" className="w-full h-full bg-cv-bg" />
        </div>

        {/* Node Inspection & Blast Radius Drawer */}
        <div className="cyber-card rounded-lg p-5 border-cv-border flex flex-col justify-between space-y-4 h-[620px] overflow-y-auto">
          <div>
            <div className="border-b border-cv-border pb-3 flex items-center justify-between">
              <h3 className="text-sm font-sans font-semibold text-cv-text flex items-center space-x-2">
                <Info className="w-4 h-4 text-cv-blue" />
                <span>NODE INSPECTION</span>
              </h3>
              {selectedNode ? (
                <Badge variant={selectedNode.criticality === 'critical' ? 'critical' : 'cyan'}>
                  {selectedNode.type?.toUpperCase()}
                </Badge>
              ) : (
                <span className="text-[10px] font-mono text-cv-muted">SELECT A NODE</span>
              )}
            </div>

            {selectedNode ? (
              <div className="space-y-4 font-mono text-xs mt-4">
                <div>
                  <h4 className="text-base font-bold text-cv-text font-sans">{selectedNode.label}</h4>
                  <p className="text-[11px] text-cv-blue mt-0.5">{selectedNode.owner || selectedNode.type}</p>
                </div>

                <div className="p-3 rounded-lg bg-cv-bg border border-cv-border space-y-2">
                  <div className="flex justify-between text-cv-muted">
                    <span>Node ID:</span>
                    <strong className="text-cv-text">{selectedNode.id}</strong>
                  </div>
                  {selectedNode.environment && (
                    <div className="flex justify-between text-cv-muted">
                      <span>Environment:</span>
                      <strong className="text-cv-text">{selectedNode.environment}</strong>
                    </div>
                  )}
                  {selectedNode.criticality && (
                    <div className="flex justify-between text-cv-muted">
                      <span>Criticality:</span>
                      <strong className="text-cv-danger uppercase">{selectedNode.criticality}</strong>
                    </div>
                  )}
                  {selectedNode.internet_exposed != null && (
                    <div className="flex justify-between text-cv-muted">
                      <span>Internet Exposed:</span>
                      <strong className={selectedNode.internet_exposed ? 'text-cv-danger' : 'text-cv-success'}>
                        {selectedNode.internet_exposed ? 'YES (Public Ingress)' : 'NO (Internal Only)'}
                      </strong>
                    </div>
                  )}
                  {selectedNode.risk_score != null && (
                    <div className="flex justify-between text-cv-muted">
                      <span>Risk Score:</span>
                      <strong className="text-cv-danger">{Number(selectedNode.risk_score).toFixed(1)} / 100</strong>
                    </div>
                  )}
                </div>

                {/* Blast Radius Section */}
                {blastRadiusData && (
                  <div className="p-3.5 rounded-lg bg-cv-warningBg border border-amber-200 space-y-2">
                    <div className="flex items-center space-x-2 text-cv-warning font-bold">
                      <Sparkles className="w-4 h-4" />
                      <span>DOWNSTREAM BLAST RADIUS</span>
                    </div>
                    <div className="text-[11px] text-cv-muted">
                      Impact surface if <strong className="text-cv-text">{selectedNode.label}</strong> is compromised:
                    </div>
                    <div className="flex justify-between text-xs pt-1 border-t border-amber-200">
                      <span className="text-cv-muted">Downstream Assets:</span>
                      <strong className="text-cv-warning">
                        {blastRadiusData.downstream_dependencies?.length || 0}
                      </strong>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-cv-muted">Impacted Services:</span>
                      <strong className="text-cv-danger">
                        {blastRadiusData.business_services?.map(s => s.name).join(', ') || NO_DATA}
                      </strong>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-cv-muted">Authorized Users:</span>
                      <strong className="text-cv-text">
                        {blastRadiusData.users_with_access?.length || 0} Accounts
                      </strong>
                    </div>
                  </div>
                )}

              </div>
            ) : (
              <div className="py-16 text-center text-cv-muted font-mono text-xs space-y-2">
                <Network className="w-8 h-8 mx-auto text-cv-border" />
                <p>Click any node to inspect real security telemetry and evaluate blast radius.</p>
              </div>
            )}
          </div>

          {selectedNode && selectedNode.db_id && (
            <div className="pt-3 border-t border-cv-border">
              <button
                onClick={calculateBlastRadius}
                disabled={loadingBlastRadius}
                className="w-full py-2 rounded-lg bg-cv-warningBg hover:bg-amber-100 text-cv-warning border border-amber-200 font-mono text-xs font-bold transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Calculate Blast Radius (API)</span>
              </button>
            </div>
          )}

        </div>

      </div>

    </div>
  );
}
