import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';
import SignalGraph from '@/components/signals/SignalGraph';
import SignalAccordion from '@/components/signals/SignalAccordion';
import { getSignalGraph, getSignalHeatmap } from '@/lib/queries';
import { SignalType } from '@/lib/types';

export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: 'Signal Observatory - WorldBrief',
  description: 'Explore the key persons, organizations, places, and themes driving global news coverage.',
};

const CATEGORIES: { type: SignalType; icon: string; badge: string }[] = [
  { type: 'persons',      icon: 'P', badge: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
  { type: 'orgs',         icon: 'O', badge: 'bg-green-500/10 text-green-400 border-green-500/20' },
  { type: 'places',       icon: 'G', badge: 'bg-orange-500/10 text-orange-400 border-orange-500/20' },
  { type: 'commodities',  icon: 'C', badge: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' },
  { type: 'policies',     icon: 'L', badge: 'bg-purple-500/10 text-purple-400 border-purple-500/20' },
  { type: 'systems',      icon: 'S', badge: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20' },
  { type: 'named_events', icon: 'E', badge: 'bg-pink-500/10 text-pink-400 border-pink-500/20' },
];

export default async function SignalObservatoryPage() {
  const [graph, heatmapSignals] = await Promise.all([
    getSignalGraph(8),
    getSignalHeatmap(8),
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

        {/* Full-width graph */}
        <div className="space-y-2">
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

        {/* Category accordion with heatmaps */}
        {heatmapSignals.length > 0 && (
          <div className="space-y-3">
            <div>
              <h2 className="text-lg font-semibold mb-1">Signal Activity</h2>
              <p className="text-xs text-dashboard-text-muted">
                Weekly event counts for top signals by category. Expand a panel to explore.
              </p>
            </div>
            <SignalAccordion signals={heatmapSignals} categories={CATEGORIES} />
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
