import { SignalStats } from '@/lib/types';

interface SignalDashboardProps {
  stats: SignalStats;
}

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-dashboard-border/30 rounded-lg p-3 text-center">
      <div className="text-2xl font-bold text-dashboard-text">{value}</div>
      <div className="text-xs text-dashboard-text-muted mt-0.5">{label}</div>
      {sub && <div className="text-[10px] text-dashboard-text-muted mt-0.5">{sub}</div>}
    </div>
  );
}

function MiniBar({ label, count, maxCount }: { label: string; count: number; maxCount: number }) {
  const pct = maxCount > 0 ? Math.round((count / maxCount) * 100) : 0;
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-24 text-dashboard-text-muted truncate" title={label}>{label}</span>
      <div className="flex-1 h-1.5 bg-dashboard-border rounded-full overflow-hidden">
        <div className="h-full bg-blue-500/60 rounded-full" style={{ width: `${pct}%` }} />
      </div>
      <span className="w-8 text-right text-dashboard-text-muted">{count}</span>
    </div>
  );
}

function LanguagePills({ distribution }: { distribution: Record<string, number> }) {
  const sorted = Object.entries(distribution).sort((a, b) => b[1] - a[1]);
  const total = sorted.reduce((s, [, v]) => s + v, 0);

  return (
    <div className="flex flex-wrap gap-1">
      {sorted.map(([lang, count]) => {
        const pct = Math.round((count / total) * 100);
        return (
          <span
            key={lang}
            className="text-[10px] px-1.5 py-0.5 rounded bg-dashboard-border text-dashboard-text-muted"
            title={`${count} titles (${pct}%)`}
          >
            {lang.toUpperCase()} {pct}%
          </span>
        );
      })}
    </div>
  );
}

export default function SignalDashboard({ stats }: SignalDashboardProps) {
  const topPublisherMax = stats.top_publishers?.[0]?.count || 1;
  const topPersonMax = stats.top_persons?.[0]?.count || 1;

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Topic Stats</h2>

      {/* Top row: key stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Headlines" value={stats.title_count} />
        <StatCard
          label="Publishers"
          value={stats.publisher_count}
          sub={`HHI ${(stats.publisher_hhi * 100).toFixed(1)}%`}
        />
        <StatCard label="Languages" value={stats.language_count} />
        <StatCard label="Date Span" value={`${stats.date_range_days}d`} />
      </div>

      {/* Top publishers + top persons side by side */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {stats.top_publishers && stats.top_publishers.length > 0 && (
          <div className="bg-dashboard-border/30 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-dashboard-text mb-3">Top Publishers</h3>
            <div className="space-y-1.5">
              {stats.top_publishers.map(p => (
                <MiniBar key={p.name} label={p.name} count={p.count} maxCount={topPublisherMax} />
              ))}
            </div>
          </div>
        )}
        {stats.top_persons && stats.top_persons.length > 0 && (
          <div className="bg-dashboard-border/30 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-dashboard-text mb-3">Top Persons</h3>
            <div className="space-y-1.5">
              {stats.top_persons.map(p => (
                <MiniBar key={p.name} label={p.name} count={p.count} maxCount={topPersonMax} />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Language distribution */}
      {stats.language_distribution && (
        <div className="bg-dashboard-border/30 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-dashboard-text mb-2">Language Distribution</h3>
          <LanguagePills distribution={stats.language_distribution} />
        </div>
      )}
    </div>
  );
}
