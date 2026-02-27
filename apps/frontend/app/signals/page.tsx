import type { Metadata } from 'next';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import SignalGraph from '@/components/signals/SignalGraph';
import TemporalHeatmap from '@/components/signals/TemporalHeatmap';
import { getSignalGraph, getSignalHeatmap } from '@/lib/queries';
import { SignalType, SIGNAL_LABELS } from '@/lib/types';

export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: 'Signal Observatory - WorldBrief',
  description: 'Explore the key persons, organizations, places, and themes driving global news coverage.',
};

const CATEGORIES: { type: SignalType; icon: string; badge: string; border: string }[] = [
  { type: 'persons',      icon: 'P', badge: 'bg-blue-500/10 text-blue-400 border-blue-500/20',   border: 'hover:border-blue-500/50' },
  { type: 'orgs',         icon: 'O', badge: 'bg-green-500/10 text-green-400 border-green-500/20',  border: 'hover:border-green-500/50' },
  { type: 'places',       icon: 'G', badge: 'bg-orange-500/10 text-orange-400 border-orange-500/20', border: 'hover:border-orange-500/50' },
  { type: 'commodities',  icon: 'C', badge: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20', border: 'hover:border-yellow-500/50' },
  { type: 'policies',     icon: 'L', badge: 'bg-purple-500/10 text-purple-400 border-purple-500/20', border: 'hover:border-purple-500/50' },
  { type: 'systems',      icon: 'S', badge: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',    border: 'hover:border-cyan-500/50' },
  { type: 'named_events', icon: 'E', badge: 'bg-pink-500/10 text-pink-400 border-pink-500/20',    border: 'hover:border-pink-500/50' },
];

export default async function SignalObservatoryPage() {
  const [graph, heatmapSignals] = await Promise.all([
    getSignalGraph(8),
    getSignalHeatmap(3),
  ]);

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-3xl md:text-4xl font-bold mb-2">Signal Observatory</h1>
          <p className="text-dashboard-text-muted">
            Key actors, institutions, and themes driving global news coverage.
          </p>
        </div>

        {/* Graph + Sidebar */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Force-directed graph */}
          <div className="lg:col-span-3 space-y-2">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Co-occurrence Network</h2>
              <p className="text-xs text-dashboard-text-muted hidden sm:block">
                Hover to highlight connections. Click a node to explore.
              </p>
            </div>
            <SignalGraph nodes={graph.nodes} edges={graph.edges} />
            <p className="text-xs text-dashboard-text-muted">
              Nodes are the most-mentioned signals across 180+ outlets over the last 30 days.
              Lines connect signals that appear in the same events. Node size reflects mention frequency.
              Colors indicate signal type: <span className="text-blue-400">persons</span>, <span className="text-green-400">organizations</span>, <span className="text-orange-400">places</span>, <span className="text-yellow-400">commodities</span>, <span className="text-purple-400">policies</span>, <span className="text-cyan-400">systems</span>, <span className="text-pink-400">events</span>.
            </p>
          </div>

          {/* Category sidebar */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider">
              Categories
            </h3>
            {CATEGORIES.map(({ type, icon, badge, border }) => {
              const count = graph.nodes.filter(n => n.signal_type === type).length;
              return (
                <Link
                  key={type}
                  href={`/signals/${type}`}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg border border-dashboard-border ${border} transition group`}
                >
                  <span className={`inline-flex items-center justify-center w-6 h-6 rounded text-xs font-bold border ${badge}`}>
                    {icon}
                  </span>
                  <span className="text-sm text-dashboard-text group-hover:text-blue-400 transition flex-1">
                    {SIGNAL_LABELS[type]}
                  </span>
                  {count > 0 && (
                    <span className="text-xs text-dashboard-text-muted">{count}</span>
                  )}
                </Link>
              );
            })}
          </div>
        </div>

        {/* Temporal Heatmap */}
        {heatmapSignals.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold mb-1">Signal Activity</h2>
            <p className="text-xs text-dashboard-text-muted mb-3">
              Weekly event counts for top signals. Brighter cells indicate higher activity.
            </p>
            <div className="p-4 rounded-lg border border-dashboard-border bg-dashboard-surface">
              <TemporalHeatmap signals={heatmapSignals} />
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
