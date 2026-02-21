import Link from 'next/link';
import { getSiblingNarratives } from '@/lib/queries';

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
    <div className="flex items-center justify-between bg-dashboard-border/30 rounded-lg px-4 py-2 mb-4 text-sm">
      <div className="w-1/3">
        {prev && (
          <Link href={`/analysis/${prev.id}`} className="text-blue-400 hover:text-blue-300 transition-colors">
            &larr; {prev.label}
          </Link>
        )}
      </div>
      <div className="text-dashboard-text-muted text-center">
        Frame {currentIdx + 1} of {siblings.length}
      </div>
      <div className="w-1/3 text-right">
        {next && (
          <Link href={`/analysis/${next.id}`} className="text-blue-400 hover:text-blue-300 transition-colors">
            {next.label} &rarr;
          </Link>
        )}
      </div>
    </div>
  );
}
