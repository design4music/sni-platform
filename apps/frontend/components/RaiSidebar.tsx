import { RaiSignals, SignalStats } from '@/lib/types';

// Convert CAPS_UNDERSCORE pipeline labels to readable text
// e.g. "US_EXECUTIVE" -> "US Executive", "FOREIGN_POLICY" -> "Foreign Policy"
function humanizeLabels(text: string): string {
  return text.replace(/\b[A-Z][A-Z_]{2,}\b/g, (match) => {
    return match.split('_').map(w =>
      w.charAt(0) + w.slice(1).toLowerCase()
    ).join(' ');
  });
}

interface RaiSidebarProps {
  signals: RaiSignals;
  stats: SignalStats | null;
}

export default function RaiSidebar({ signals, stats }: RaiSidebarProps) {
  const pct = Math.round(signals.adequacy * 100);
  const color = signals.adequacy >= 0.7 ? 'green' : signals.adequacy >= 0.4 ? 'yellow' : 'red';
  const barColor = { green: 'bg-green-500', yellow: 'bg-yellow-500', red: 'bg-red-500' }[color];
  const badgeColor = {
    green: 'bg-green-500/20 text-green-400 border-green-500/30',
    yellow: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    red: 'bg-red-500/20 text-red-400 border-red-500/30',
  }[color];

  const concConfig: Record<string, { label: string; cls: string }> = {
    ok: { label: 'Diverse', cls: 'bg-green-500/20 text-green-400 border-green-500/30' },
    warning: { label: 'Concentrated', cls: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30' },
    critical: { label: 'Highly Concentrated', cls: 'bg-red-500/20 text-red-400 border-red-500/30' },
  };
  const conc = concConfig[signals.source_concentration] || concConfig.ok;

  return (
    <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4 space-y-4">
      <h3 className="text-lg font-semibold text-dashboard-text">Coverage Assessment</h3>

      {/* Adequacy */}
      <div>
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-xs font-semibold text-dashboard-text-muted uppercase tracking-wide">Representation</span>
          <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${badgeColor}`}>
            {pct}%
          </span>
        </div>
        <div className="h-1.5 bg-dashboard-border rounded-full overflow-hidden mb-2">
          <div className={`h-full ${barColor} rounded-full`} style={{ width: `${pct}%` }} />
        </div>
        <p className="text-xs text-dashboard-text-muted leading-relaxed">{humanizeLabels(signals.adequacy_reason)}</p>
      </div>

      {/* Source Concentration */}
      <div>
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-xs font-semibold text-dashboard-text-muted uppercase tracking-wide">Sources</span>
          <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${conc.cls}`}>
            {conc.label}
          </span>
        </div>
        {stats && (
          <p className="text-xs text-dashboard-text-muted">
            {stats.publisher_count} publishers, {stats.language_count} languages
          </p>
        )}
      </div>

      {/* Framing Bias */}
      {signals.framing_bias && (
        <div>
          <h4 className="text-xs font-semibold text-dashboard-text-muted uppercase tracking-wide mb-1.5">
            Framing Bias
          </h4>
          <p className="text-xs text-dashboard-text-muted leading-relaxed">{humanizeLabels(signals.framing_bias)}</p>
        </div>
      )}

      {/* Key Findings */}
      {signals.findings && signals.findings.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-dashboard-text-muted uppercase tracking-wide mb-1.5">
            Key Findings
          </h4>
          <ul className="space-y-1">
            {signals.findings.map((f, i) => (
              <li key={i} className="text-xs text-dashboard-text-muted leading-relaxed flex items-start gap-1.5">
                <span className="text-blue-400 mt-0.5 flex-shrink-0">-</span>
                <span>{humanizeLabels(f)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Geographic Blind Spots */}
      {signals.geographic_blind_spots && signals.geographic_blind_spots.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-dashboard-text-muted uppercase tracking-wide mb-1.5">
            Blind Spots
          </h4>
          <ul className="space-y-1">
            {signals.geographic_blind_spots.map((s, i) => (
              <li key={i} className="text-xs text-dashboard-text-muted leading-relaxed flex items-start gap-1.5">
                <span className="text-orange-400 mt-0.5 flex-shrink-0">?</span>
                <span>{humanizeLabels(s)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Missing Perspectives */}
      {signals.missing_perspectives && signals.missing_perspectives.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-dashboard-text-muted uppercase tracking-wide mb-1.5">
            Missing Perspectives
          </h4>
          <ul className="space-y-1">
            {signals.missing_perspectives.map((p, i) => (
              <li key={i} className="text-xs text-dashboard-text-muted leading-relaxed flex items-start gap-1.5">
                <span className="text-orange-400 mt-0.5 flex-shrink-0">?</span>
                <span>{humanizeLabels(p)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Follow the Gain */}
      {signals.follow_the_gain && (
        <div>
          <h4 className="text-xs font-semibold text-dashboard-text-muted uppercase tracking-wide mb-1.5">
            Follow the Gain
          </h4>
          <p className="text-xs text-dashboard-text-muted leading-relaxed">{humanizeLabels(signals.follow_the_gain)}</p>
        </div>
      )}
    </div>
  );
}
