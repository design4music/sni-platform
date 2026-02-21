import Link from 'next/link';
import { getSiblingNarratives } from '@/lib/queries';

const DOT_COLORS = [
  'bg-red-500',
  'bg-blue-500',
  'bg-amber-500',
  'bg-green-500',
  'bg-purple-500',
];

const LABELS = ['Critical', 'Neutral', 'Supportive', 'Alternate', 'Minor'];

interface Props {
  currentNarrativeId: string;
  entityType: string;
  entityId: string;
}

export default async function NarrativeNav({ currentNarrativeId, entityType, entityId }: Props) {
  const siblings = await getSiblingNarratives(entityType, entityId);
  if (siblings.length <= 1) return null;

  const currentIdx = siblings.findIndex(s => s.id === currentNarrativeId);
  if (currentIdx === -1) return null;

  const prev = currentIdx > 0 ? siblings[currentIdx - 1] : null;
  const next = currentIdx < siblings.length - 1 ? siblings[currentIdx + 1] : null;

  return (
    <nav className="flex items-center justify-between bg-dashboard-border/30 rounded-lg px-3 py-2 mb-4">
      {/* Prev arrow */}
      {prev ? (
        <Link
          href={`/analysis/${prev.id}`}
          className="text-xl leading-none text-blue-400 hover:text-blue-300 transition-colors px-1"
          aria-label="Previous frame"
        >
          &#x2039;
        </Link>
      ) : (
        <span className="text-xl leading-none text-dashboard-border px-1">&#x2039;</span>
      )}

      {/* Dot stepper */}
      <div className="flex items-center gap-2">
        {siblings.map((s, i) => {
          const color = DOT_COLORS[i % DOT_COLORS.length];
          const label = LABELS[i] || `Frame ${i + 1}`;
          const isCurrent = i === currentIdx;

          return isCurrent ? (
            <span key={s.id} className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-dashboard-border/60">
              <span className={`w-2 h-2 rounded-full ${color}`} />
              <span className="text-xs font-medium text-dashboard-text">{label}</span>
            </span>
          ) : (
            <Link
              key={s.id}
              href={`/analysis/${s.id}`}
              className="flex items-center gap-1 px-1.5 py-0.5 rounded-full hover:bg-dashboard-border/40 transition-colors"
              title={s.label}
            >
              <span className={`w-2 h-2 rounded-full ${color} opacity-50`} />
              <span className="text-xs text-dashboard-text-muted hidden sm:inline">{label}</span>
            </Link>
          );
        })}
      </div>

      {/* Next arrow */}
      {next ? (
        <Link
          href={`/analysis/${next.id}`}
          className="text-xl leading-none text-blue-400 hover:text-blue-300 transition-colors px-1"
          aria-label="Next frame"
        >
          &#x203a;
        </Link>
      ) : (
        <span className="text-xl leading-none text-dashboard-border px-1">&#x203a;</span>
      )}
    </nav>
  );
}
