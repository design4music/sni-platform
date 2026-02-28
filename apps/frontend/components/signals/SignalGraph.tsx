'use client';

import { useCallback, useRef, useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import { SignalNode, SignalEdge, SignalType } from '@/lib/types';

const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false });

const TYPE_COLORS: Record<SignalType, string> = {
  persons: '#60a5fa',
  orgs: '#4ade80',
  places: '#fb923c',
  commodities: '#facc15',
  policies: '#a78bfa',
  systems: '#22d3ee',
  named_events: '#f472b6',
};

const TYPE_LABELS: Record<SignalType, string> = {
  persons: 'Person',
  orgs: 'Org',
  places: 'Place',
  commodities: 'Commodity',
  policies: 'Policy',
  systems: 'System',
  named_events: 'Event',
};

interface GraphNode {
  id: string;
  label: string;
  signal_type: SignalType;
  event_count: number;
  context?: string;
}

interface GraphLink {
  source: string;
  target: string;
  weight: number;
}

interface Props {
  nodes: SignalNode[];
  edges: SignalEdge[];
}

export default function SignalGraph({ nodes, edges }: Props) {
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const graphRef = useRef<any>(null);
  const forceConfigured = useRef(false);
  const [dimensions, setDimensions] = useState({ width: 600, height: 500 });
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  useEffect(() => {
    function updateSize() {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setDimensions({ width: rect.width, height: Math.max(rect.width * 0.45, 400) });
      }
    }
    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  // Memoize graph data — prevents simulation restart on re-render
  const graphData = useMemo(() => {
    const gNodes: GraphNode[] = nodes.map(n => ({
      id: `${n.signal_type}:${n.value}`,
      label: n.value,
      signal_type: n.signal_type,
      event_count: n.event_count,
      context: n.context,
    }));
    const nodeIds = new Set(gNodes.map(n => n.id));
    const gLinks: GraphLink[] = edges
      .filter(e => nodeIds.has(`${e.source_type}:${e.source}`) && nodeIds.has(`${e.target_type}:${e.target}`))
      .map(e => ({
        source: `${e.source_type}:${e.source}`,
        target: `${e.target_type}:${e.target}`,
        weight: e.weight,
      }));
    return { nodes: gNodes, links: gLinks };
  }, [nodes, edges]);

  // Adjacency set for hover highlighting
  const adjacency = useMemo(() => {
    const adj = new Set<string>();
    for (const link of graphData.links) {
      adj.add(`${link.source}|${link.target}`);
      adj.add(`${link.target}|${link.source}`);
    }
    return adj;
  }, [graphData]);

  // Sizing
  const { minCount, countRange } = useMemo(() => {
    const counts = nodes.map(n => n.event_count);
    const mn = Math.min(...counts, 1);
    const mx = Math.max(...counts, 1);
    return { minCount: mn, countRange: mx - mn || 1 };
  }, [nodes]);

  function nodeRadius(count: number): number {
    const normalized = (count - minCount) / countRange;
    return 6 + Math.pow(normalized, 0.5) * 24;
  }

  // Poll until graph ref is available, then configure forces once
  useEffect(() => {
    if (forceConfigured.current) return;
    const id = setInterval(() => {
      const fg = graphRef.current;
      if (!fg) return;
      const charge = fg.d3Force('charge');
      if (!charge) return;
      charge.strength(-300);
      fg.d3Force('link')?.distance(100);
      fg.d3ReheatSimulation();
      forceConfigured.current = true;
      clearInterval(id);
    }, 50);
    return () => clearInterval(id);
  }, []);

  const nodeCanvasObject = useCallback((node: GraphNode, ctx: CanvasRenderingContext2D) => {
    const r = nodeRadius(node.event_count);
    const color = TYPE_COLORS[node.signal_type] || '#94a3b8';
    const x = (node as unknown as { x: number }).x;
    const y = (node as unknown as { y: number }).y;
    const isHovered = hoveredNode === node.id;
    const isNeighbor = hoveredNode ? adjacency.has(`${hoveredNode}|${node.id}`) : false;
    const dimmed = hoveredNode && !isHovered && !isNeighbor;

    // Outer glow
    ctx.beginPath();
    ctx.arc(x, y, r + (isHovered ? 6 : 3), 0, 2 * Math.PI);
    ctx.fillStyle = color + (isHovered ? '33' : '15');
    ctx.fill();

    // Circle
    ctx.beginPath();
    ctx.arc(x, y, r, 0, 2 * Math.PI);
    ctx.fillStyle = dimmed ? color + '18' : color + '55';
    ctx.strokeStyle = dimmed ? color + '30' : color;
    ctx.lineWidth = isHovered ? 2.5 : 1.5;
    ctx.fill();
    ctx.stroke();

    // Label
    const fontSize = Math.max(10, Math.min(13, r * 0.7));
    ctx.font = `${isHovered ? 'bold ' : ''}${fontSize}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillStyle = dimmed ? '#64748b' : '#e2e8f0';
    ctx.fillText(node.label, x, y + r + 4);

    if (isHovered) {
      ctx.font = '9px sans-serif';
      ctx.fillStyle = color;
      ctx.fillText(`${TYPE_LABELS[node.signal_type]} | ${node.event_count} events`, x, y + r + 4 + fontSize + 2);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hoveredNode, minCount, countRange, adjacency]);

  const linkCanvasObject = useCallback((link: GraphLink, ctx: CanvasRenderingContext2D) => {
    const sourceNode = link.source as unknown as { x: number; y: number; id: string };
    const targetNode = link.target as unknown as { x: number; y: number; id: string };
    if (!sourceNode.x || !targetNode.x) return;

    const sourceId = sourceNode.id;
    const targetId = targetNode.id;
    const isHighlighted = hoveredNode && (hoveredNode === sourceId || hoveredNode === targetId);
    const dimmed = hoveredNode && !isHighlighted;

    ctx.beginPath();
    ctx.moveTo(sourceNode.x, sourceNode.y);
    ctx.lineTo(targetNode.x, targetNode.y);

    if (isHighlighted) {
      ctx.strokeStyle = '#94a3b8';
      ctx.lineWidth = Math.max(1.5, Math.min(3, link.weight / 4));
    } else if (dimmed) {
      ctx.strokeStyle = '#1e293b44';
      ctx.lineWidth = 0.3;
    } else {
      ctx.strokeStyle = '#33415588';
      ctx.lineWidth = 0.7;
    }
    ctx.stroke();
  }, [hoveredNode]);

  const handleNodeHover = useCallback((node: GraphNode | null) => {
    setHoveredNode(node ? node.id : null);
  }, []);

  const handleNodeClick = useCallback((node: GraphNode) => {
    router.push(`/signals/${node.signal_type}/${encodeURIComponent(node.label)}`);
  }, [router]);

  return (
    <div ref={containerRef} className="w-full rounded-lg border border-dashboard-border bg-[#0f172a] overflow-hidden [&_canvas]:cursor-pointer">
      {dimensions.width > 0 && (
        <ForceGraph2D
          ref={graphRef}
          graphData={graphData}
          width={dimensions.width}
          height={dimensions.height}
          backgroundColor="#0f172a"
          nodeCanvasObject={nodeCanvasObject as never}
          nodePointerAreaPaint={((node: GraphNode, color: string, ctx: CanvasRenderingContext2D) => {
            const r = nodeRadius(node.event_count);
            const x = (node as unknown as { x: number }).x;
            const y = (node as unknown as { y: number }).y;
            ctx.beginPath();
            ctx.arc(x, y, r + 6, 0, 2 * Math.PI);
            ctx.fillStyle = color;
            ctx.fill();
          }) as never}
          linkCanvasObject={linkCanvasObject as never}
          linkCanvasObjectMode={() => 'replace'}
          onNodeHover={handleNodeHover as never}
          onNodeClick={handleNodeClick as never}
          onNodeDrag={() => {/* allow dragging individual nodes */}}
          cooldownTime={Infinity}
          d3AlphaDecay={0.005}
          d3AlphaMin={0}
          d3VelocityDecay={0.4}
          enableNodeDrag={true}
          enableZoomInteraction={true}
          enablePanInteraction={true}
        />
      )}
    </div>
  );
}
