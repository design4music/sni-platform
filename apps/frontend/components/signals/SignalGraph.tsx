'use client';

import { useCallback, useRef, useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { SignalNode, SignalEdge, SignalType } from '@/lib/types';

// react-force-graph-2d uses canvas, must be client-only
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
  onNodeClick?: (node: SignalNode) => void;
}

export default function SignalGraph({ nodes, edges, onNodeClick }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 600, height: 450 });

  useEffect(() => {
    function updateSize() {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setDimensions({ width: rect.width, height: Math.max(rect.width * 0.6, 350) });
      }
    }
    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  const graphNodes: GraphNode[] = nodes.map(n => ({
    id: `${n.signal_type}:${n.value}`,
    label: n.value,
    signal_type: n.signal_type,
    event_count: n.event_count,
    context: n.context,
  }));

  const nodeIds = new Set(graphNodes.map(n => n.id));
  const graphLinks: GraphLink[] = edges
    .filter(e => nodeIds.has(`${e.source_type}:${e.source}`) && nodeIds.has(`${e.target_type}:${e.target}`))
    .map(e => ({
      source: `${e.source_type}:${e.source}`,
      target: `${e.target_type}:${e.target}`,
      weight: e.weight,
    }));

  const maxCount = Math.max(...nodes.map(n => n.event_count), 1);

  const nodeCanvasObject = useCallback((node: GraphNode, ctx: CanvasRenderingContext2D) => {
    const r = 4 + Math.sqrt(node.event_count / maxCount) * 14;
    const color = TYPE_COLORS[node.signal_type] || '#94a3b8';
    const x = (node as unknown as { x: number }).x;
    const y = (node as unknown as { y: number }).y;

    // Glow
    ctx.beginPath();
    ctx.arc(x, y, r + 2, 0, 2 * Math.PI);
    ctx.fillStyle = color + '22';
    ctx.fill();

    // Circle
    ctx.beginPath();
    ctx.arc(x, y, r, 0, 2 * Math.PI);
    ctx.fillStyle = color + '44';
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    ctx.fill();
    ctx.stroke();

    // Label
    const fontSize = Math.max(9, Math.min(12, r * 0.8));
    ctx.font = `${fontSize}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillStyle = '#e2e8f0';
    ctx.fillText(node.label, x, y + r + 3);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [maxCount]);

  const handleNodeClick = useCallback((node: GraphNode) => {
    if (onNodeClick) {
      const original = nodes.find(n => n.signal_type === node.signal_type && n.value === node.label);
      if (original) onNodeClick(original);
    }
  }, [nodes, onNodeClick]);

  return (
    <div ref={containerRef} className="w-full rounded-lg border border-dashboard-border bg-[#0f172a] overflow-hidden">
      {dimensions.width > 0 && (
        <ForceGraph2D
          graphData={{ nodes: graphNodes, links: graphLinks }}
          width={dimensions.width}
          height={dimensions.height}
          backgroundColor="#0f172a"
          nodeCanvasObject={nodeCanvasObject as never}
          nodePointerAreaPaint={((node: GraphNode, color: string, ctx: CanvasRenderingContext2D) => {
            const r = 4 + Math.sqrt(node.event_count / maxCount) * 14;
            const x = (node as unknown as { x: number }).x;
            const y = (node as unknown as { y: number }).y;
            ctx.beginPath();
            ctx.arc(x, y, r + 4, 0, 2 * Math.PI);
            ctx.fillStyle = color;
            ctx.fill();
          }) as never}
          linkColor={() => '#33415566'}
          linkWidth={((link: GraphLink) => Math.max(0.5, Math.min(3, link.weight / 5))) as never}
          onNodeClick={handleNodeClick as never}
          cooldownTime={3000}
          d3AlphaDecay={0.04}
          d3VelocityDecay={0.3}
          enableZoomInteraction={true}
          enablePanInteraction={true}
        />
      )}
    </div>
  );
}
