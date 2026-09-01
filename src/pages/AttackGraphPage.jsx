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
  Filter,
  Eye,
  Zap,
  Info,
  DollarSign,
  Lock,
  Layers,
  Sparkles,
  ArrowRight
} from 'lucide-react';
import Badge from '../components/common/Badge';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { useTelemetry } from '../context/TelemetryContext';
import { attackGraphApi } from '../api/attackGraphApi';

try {
  cytoscape.use(dagre);
  cytoscape.use(cola);
} catch (e) {}

export default function AttackGraphPage() {
  const { formatCurrency, refreshKey } = useTelemetry();
  const containerRef = useRef(null);
  const cyRef = useRef(null);

  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [selectedNode, setSelectedNode] = useState(null);
  const [activeLayout, setActiveLayout] = useState('breadthfirst');
  const [highlightKillchain, setHighlightKillchain] = useState(true);
  const [blastRadiusActive, setBlastRadiusActive] = useState(false);
  const [blastRadiusCount, setBlastRadiusCount] = useState(0);
  const [blastRadiusExposure, setBlastRadiusExposure] = useState(0);
  const [filterTier, setFilterTier] = useState('ALL');

  useEffect(() => {
    async function loadGraph() {
      try {
        setLoading(true);
        const data = await attackGraphApi.getGraphTopology();
        setGraphData(data);
        setError(null);
      } catch (err) {
        console.error('Failed to load attack graph topology:', err);
        setError('Failed to fetch attack graph topology.');
      } finally {
        setLoading(false);
      }
    }
    loadGraph();
  }, [refreshKey]);

  useEffect(() => {
    if (!graphData || !containerRef.current) return;

    const cy = cytoscape({
      container: containerRef.current,
      elements: graphData.elements,
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'color': '#17212B',
            'font-family': 'Inter',
            'font-size': '11px',
            'font-weight': 'bold',
            'text-valign': 'bottom',
            'text-margin-y': 6,
            'background-color': '#E4E7EC',
            'border-width': 2,
            'border-color': '#94A3B8',
            'width': 44,
            'height': 44,
            'transition-property': 'background-color, border-color, border-width',
            'transition-duration': '0.2s',
          }
        },
        {
          selector: 'node[type="internet"]',
          style: {
            'background-color': '#94A3B8',
            'border-color': '#64748B',
            'shape': 'round-rectangle',
            'width': 50,
            'height': 50,
          }
        },
        {
          selector: 'node[type="vpn"]',
          style: {
            'background-color': '#FEE2E2',
            'border-color': '#DC2626',
            'border-width': 3,
            'shape': 'diamond',
            'width': 48,
            'height': 48,
          }
        },
        {
          selector: 'node[type="server"]',
          style: {
            'background-color': '#DBEAFE',
            'border-color': '#2563EB',
            'shape': 'round-rectangle',
          }
        },
        {
          selector: 'node[type="user"]',
          style: {
            'background-color': '#EDE9FE',
            'border-color': '#7C3AED',
            'shape': 'ellipse',
            'width': 46,
            'height': 46,
          }
        },
        {
          selector: 'node[type="database"]',
          style: {
            'background-color': '#FEE2E2',
            'border-color': '#DC2626',
            'border-width': 3,
            'shape': 'barrel',
            'width': 52,
            'height': 52,
          }
        },
        {
          selector: 'node[type="service"]',
          style: {
            'background-color': '#DCFCE7',
            'border-color': '#16A34A',
            'shape': 'hexagon',
            'width': 52,
            'height': 52,
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#CBD5E1',
            'target-arrow-color': '#CBD5E1',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'arrow-scale': 1.2,
            'label': 'data(protocol)',
            'font-family': 'JetBrains Mono',
            'font-size': '8px',
            'color': '#94A3B8',
            'text-rotation': 'autorotate',
            'text-margin-y': -8
          }
        },
        {
          selector: 'edge[isAttackPath]',
          style: {
            'line-color': '#DC2626',
            'target-arrow-color': '#DC2626',
            'width': 3.5,
            'line-style': 'dashed',
            'color': '#EF4444',
          }
        },
        {
          selector: '.highlighted-node',
          style: {
            'border-color': '#DC2626',
            'border-width': 4,
            'background-color': '#FEE2E2',
          }
        },
        {
          selector: '.blast-node',
          style: {
            'border-color': '#D97706',
            'border-width': 3,
            'background-color': '#FEF3C7',
          }
        },
        {
          selector: '.dimmed',
          style: {
            'opacity': 0.25
          }
        }
      ],
      layout: getLayoutConfig(activeLayout),
    });

    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      const nodeData = node.data();
      setSelectedNode(nodeData);
      cy.elements().removeClass('highlighted-node dimmed blast-node');
      node.addClass('highlighted-node');
    });

    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        setSelectedNode(null);
        setBlastRadiusActive(false);
        cy.elements().removeClass('highlighted-node dimmed blast-node');
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
      return { name: 'breadthfirst', directed: true, roots: '#internet', padding: 40, spacingFactor: 1.4, animate: true, animationDuration: 500 };
    }
    if (name === 'concentric') {
      return {
        name: 'concentric',
        concentric: (node) => {
          if (node.data('type') === 'internet') return 5;
          if (node.data('type') === 'vpn') return 4;
          if (node.data('type') === 'server') return 3;
          if (node.data('type') === 'user') return 2;
          return 1;
        },
        levelWidth: () => 1,
        padding: 40,
        animate: true,
      };
    }
    if (name === 'cola') {
      return { name: 'cola', maxSimulationTime: 1500, fit: true, padding: 40 };
    }
    return { name: 'cose', animate: true, padding: 40 };
  }

  const triggerKillchainHighlight = () => {
    if (!cyRef.current) return;
    const cy = cyRef.current;
    
    if (highlightKillchain) {
      cy.elements().removeClass('dimmed highlighted-node blast-node');
      const attackEdges = cy.edges('[isAttackPath]');
      const connectedNodes = attackEdges.connectedNodes();
      cy.elements().addClass('dimmed');
      attackEdges.removeClass('dimmed');
      connectedNodes.removeClass('dimmed').addClass('highlighted-node');
      const vpnNode = cy.nodes('#vpn-gw');
      if (vpnNode.length) setSelectedNode(vpnNode.data());
    } else {
      cy.elements().removeClass('dimmed highlighted-node blast-node');
    }
    setHighlightKillchain(!highlightKillchain);
  };

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

    let totalExposure = selectedNode.financialRisk || 0;
    downstreamNodes.forEach(n => { totalExposure += n.data('financialRisk') || 0; });

    setBlastRadiusActive(true);
    setBlastRadiusCount(downstreamNodes.length);
    setBlastRadiusExposure(totalExposure);
  };

  const handleZoom = (factor) => {
    if (cyRef.current) {
      cyRef.current.zoom({
        level: cyRef.current.zoom() * factor,
        renderedPosition: { x: cyRef.current.width() / 2, y: cyRef.current.height() / 2 },
      });
    }
  };

  const handleFit = () => {
    if (cyRef.current) cyRef.current.fit(null, 40);
  };

  if (loading) return <LoadingSpinner text="Rendering Cytoscape Attack Graph & Lateral Movement Vectors..." />;
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
              CYTOSCAPE.JS INTERACTIVE TOPOLOGY
            </span>
            <span className="text-xs font-mono text-cv-muted">
              Full Exploitation Paths • Blast Radius Simulator
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-cv-text mt-1 tracking-tight">
            Interactive Cyber Attack Graph & Blast Radius
          </h1>
          <p className="text-xs sm:text-sm text-cv-muted mt-0.5">
            Visualize perimeter exploitation, credential theft, lateral movement, and Crown Jewel blast radiuses.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={triggerKillchainHighlight}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-lg bg-cv-dangerBg border border-red-300 text-cv-danger hover:bg-red-100 font-mono text-xs font-semibold transition-all"
          >
            <Zap className="w-4 h-4" />
            <span>HIGHLIGHT KILLCHAIN</span>
          </button>

          {selectedNode && (
            <button
              onClick={simulateBlastRadius}
              className="flex items-center space-x-2 px-3.5 py-2 rounded-lg bg-cv-warningBg border border-amber-300 text-cv-warning hover:bg-amber-100 font-mono text-xs font-semibold transition-all"
            >
              <Sparkles className="w-4 h-4" />
              <span>CALCULATE BLAST RADIUS</span>
            </button>
          )}
        </div>
      </div>

      {/* Killchain Alert Banner */}
      <div className="p-3.5 rounded-lg bg-red-50 border border-red-200 flex flex-col md:flex-row md:items-center justify-between gap-3 font-mono text-xs text-cv-muted">
        <div className="flex items-center space-x-3">
          <ShieldAlert className="w-5 h-5 text-cv-danger flex-shrink-0" />
          <div>
            <span className="text-cv-danger font-bold">FASTEST ACTIVE KILLCHAIN: </span>
            <span className="text-cv-text">{graphData.killchainSummary.fastestAttackPath}</span>
          </div>
        </div>
        <div className="flex items-center space-x-4 text-[11px] text-cv-muted">
          <span>Est. Time: <strong className="text-cv-warning">{graphData.killchainSummary.estimatedTimeToCompromise}</strong></span>
          <span>Loss at Risk: <strong className="text-cv-danger">{graphData.killchainSummary.financialExposureAtRisk}</strong></span>
        </div>
      </div>

      {/* Main Canvas & Inspection Drawer */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        
        {/* Cytoscape Canvas */}
        <div className="lg:col-span-3 cyber-card rounded-lg border-cv-border overflow-hidden relative flex flex-col h-[600px]">
          
          {/* Canvas Floating Toolbar */}
          <div className="absolute top-3 left-3 z-20 flex flex-wrap items-center gap-2 bg-white/95 p-1.5 rounded-lg border border-cv-border shadow-card backdrop-blur-md font-mono text-xs">
            <span className="text-cv-muted px-2 text-[10px] uppercase font-bold">Layout:</span>
            <button
              onClick={() => changeLayout('breadthfirst')}
              className={`px-2.5 py-1 rounded-lg transition-colors ${activeLayout === 'breadthfirst' ? 'bg-cv-blue text-white font-bold' : 'text-cv-muted hover:text-cv-text'}`}
            >
              Hierarchical
            </button>
            <button
              onClick={() => changeLayout('concentric')}
              className={`px-2.5 py-1 rounded-lg transition-colors ${activeLayout === 'concentric' ? 'bg-cv-blue text-white font-bold' : 'text-cv-muted hover:text-cv-text'}`}
            >
              Concentric Tiers
            </button>
            <button
              onClick={() => changeLayout('cola')}
              className={`px-2.5 py-1 rounded-lg transition-colors ${activeLayout === 'cola' ? 'bg-cv-blue text-white font-bold' : 'text-cv-muted hover:text-cv-text'}`}
            >
              Physics (Cola)
            </button>
          </div>

          {/* Zoom / Navigation Controls */}
          <div className="absolute top-3 right-3 z-20 flex items-center space-x-1.5 bg-white/95 p-1.5 rounded-lg border border-cv-border shadow-card backdrop-blur-md">
            <button onClick={() => handleZoom(1.2)} className="p-1.5 text-cv-muted hover:text-cv-blue rounded hover:bg-cv-bg" title="Zoom In">
              <ZoomIn className="w-4 h-4" />
            </button>
            <button onClick={() => handleZoom(0.8)} className="p-1.5 text-cv-muted hover:text-cv-blue rounded hover:bg-cv-bg" title="Zoom Out">
              <ZoomOut className="w-4 h-4" />
            </button>
            <button onClick={handleFit} className="p-1.5 text-cv-muted hover:text-cv-blue rounded hover:bg-cv-bg" title="Fit to Viewport">
              <Maximize2 className="w-4 h-4" />
            </button>
          </div>

          {/* Canvas Legend */}
          <div className="absolute bottom-3 left-3 z-20 hidden sm:flex items-center space-x-3 bg-white/95 px-3 py-2 rounded-lg border border-cv-border shadow-card backdrop-blur-md font-mono text-[10px] text-cv-muted">
            <span className="flex items-center"><span className="w-2.5 h-2.5 bg-slate-400 rounded mr-1" />Internet</span>
            <span className="flex items-center"><span className="w-2.5 h-2.5 bg-red-400 rotate-45 mr-1" />Vulnerable VPN</span>
            <span className="flex items-center"><span className="w-2.5 h-2.5 bg-blue-500 rounded mr-1" />DMZ Server</span>
            <span className="flex items-center"><span className="w-2.5 h-2.5 bg-purple-500 rounded-full mr-1" />Compromised User</span>
            <span className="flex items-center"><span className="w-2.5 h-2.5 bg-red-600 rounded mr-1" />Crown Jewel DB</span>
            <span className="flex items-center"><span className="w-2.5 h-2.5 bg-green-500 rounded mr-1" />Business Service</span>
          </div>

          {/* Cytoscape Container */}
          <div ref={containerRef} id="cy-container" className="w-full h-full bg-cv-bg" />
        </div>

        {/* Node Inspection / Blast Radius Drawer */}
        <div className="cyber-card rounded-lg p-5 border-cv-border flex flex-col justify-between space-y-4 h-[600px] overflow-y-auto">
          
          <div>
            <div className="border-b border-cv-border pb-3 flex items-center justify-between">
              <h3 className="text-sm font-sans font-semibold text-cv-text flex items-center space-x-2">
                <Info className="w-4 h-4 text-cv-blue" />
                <span>NODE INSPECTION</span>
              </h3>
              {selectedNode ? (
                <Badge variant={selectedNode.criticality === 'CRITICAL' ? 'critical' : 'cyan'}>
                  {selectedNode.type?.toUpperCase()}
                </Badge>
              ) : (
                <span className="text-[10px] font-mono text-cv-muted">NO NODE SELECTED</span>
              )}
            </div>

            {selectedNode ? (
              <div className="space-y-4 font-mono text-xs mt-4">
                <div>
                  <h4 className="text-base font-bold text-cv-text font-sans">{selectedNode.label}</h4>
                  <p className="text-[11px] text-cv-blue mt-0.5">{selectedNode.ip || selectedNode.role || 'Perimeter Gateway'}</p>
                </div>

                <div className="p-3 rounded-lg bg-cv-bg border border-cv-border space-y-2">
                  <div className="flex justify-between text-cv-muted">
                    <span>Tier:</span>
                    <strong className="text-cv-text">{selectedNode.tier}</strong>
                  </div>
                  <div className="flex justify-between text-cv-muted">
                    <span>Status:</span>
                    <strong className="text-cv-danger">{selectedNode.status}</strong>
                  </div>
                  {selectedNode.cve && (
                    <div className="flex justify-between text-cv-muted">
                      <span>Vulnerability:</span>
                      <strong className="text-cv-danger">{selectedNode.cve}</strong>
                    </div>
                  )}
                  {selectedNode.cvss && (
                    <div className="flex justify-between text-cv-muted">
                      <span>CVSS / EPSS:</span>
                      <strong className="text-cv-warning">{selectedNode.cvss} ({selectedNode.epss})</strong>
                    </div>
                  )}
                  {selectedNode.financialRisk && (
                    <div className="flex justify-between text-cv-muted">
                      <span>Direct Exposure:</span>
                      <strong className="text-cv-text">{formatCurrency(selectedNode.financialRisk)}</strong>
                    </div>
                  )}
                </div>

                {/* Blast Radius Calculation Output */}
                {blastRadiusActive && (
                  <div className="p-3.5 rounded-lg bg-cv-warningBg border border-amber-200 space-y-2">
                    <div className="flex items-center space-x-2 text-cv-warning font-bold">
                      <Sparkles className="w-4 h-4" />
                      <span>DOWNSTREAM BLAST RADIUS</span>
                    </div>
                    <div className="text-[11px] text-cv-muted">
                      If <strong className="text-cv-text">{selectedNode.label}</strong> is fully compromised:
                    </div>
                    <div className="flex justify-between text-xs pt-1 border-t border-amber-200">
                      <span className="text-cv-muted">Reachable Assets:</span>
                      <strong className="text-cv-warning">{blastRadiusCount} Hosts & Services</strong>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-cv-muted">Aggregate Loss at Risk:</span>
                      <strong className="text-cv-danger">{formatCurrency(blastRadiusExposure)}</strong>
                    </div>
                  </div>
                )}

                {/* MITRE ATT&CK Mapping */}
                <div className="space-y-1.5">
                  <span className="text-[10px] text-cv-muted uppercase font-bold">MITRE ATT&CK Techniques:</span>
                  <div className="flex flex-wrap gap-1.5">
                    <span className="px-2 py-0.5 rounded bg-cv-bg border border-cv-border text-[10px] text-cv-muted">T1190 Exploit Public-Facing</span>
                    <span className="px-2 py-0.5 rounded bg-cv-bg border border-cv-border text-[10px] text-cv-muted">T1078 Valid Accounts</span>
                    <span className="px-2 py-0.5 rounded bg-cv-bg border border-cv-border text-[10px] text-cv-muted">T1021 Lateral RDP</span>
                  </div>
                </div>

              </div>
            ) : (
              <div className="py-16 text-center text-cv-muted font-mono text-xs space-y-2">
                <Network className="w-8 h-8 mx-auto text-cv-border" />
                <p>Click any node or edge in the graph to inspect technical telemetry and compute blast radius.</p>
              </div>
            )}
          </div>

          {selectedNode && (
            <div className="pt-3 border-t border-cv-border space-y-2">
              <button
                onClick={simulateBlastRadius}
                className="w-full py-2 rounded-lg bg-cv-warningBg hover:bg-amber-100 text-cv-warning border border-amber-200 font-mono text-xs font-bold transition-all flex items-center justify-center space-x-2"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Simulate Blast Radius</span>
              </button>
            </div>
          )}

        </div>

      </div>

    </div>
  );
}
