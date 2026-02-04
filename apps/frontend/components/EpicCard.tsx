import Link from 'next/link';
import { Epic } from '@/lib/types';

interface EpicCardProps {
  epic: Epic;
}

export default function EpicCard({ epic }: EpicCardProps) {
  const truncatedSummary = epic.summary
    ? epic.summary.length > 150
      ? epic.summary.slice(0, 150) + '...'
      : epic.summary
    : null;

  return (
    <Link
      href={`/epics/${epic.slug}`}
      className="block p-6 border border-dashboard-border bg-dashboard-surface rounded-lg hover:border-blue-500 transition"
    >
      <h3 className="text-lg font-semibold mb-2">
        {epic.title || epic.anchor_tags.join(', ')}
      </h3>

      <div className="flex flex-wrap gap-3 text-xs text-dashboard-text-muted mb-3">
        <span>{epic.centroid_count} countries</span>
        <span>{epic.event_count} topics</span>
        <span>{epic.total_sources} sources</span>
      </div>

      {epic.anchor_tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {epic.anchor_tags.slice(0, 5).map(tag => (
            <span
              key={tag}
              className="text-xs px-2 py-0.5 rounded bg-dashboard-border text-dashboard-text-muted"
            >
              {tag}
            </span>
          ))}
          {epic.anchor_tags.length > 5 && (
            <span className="text-xs px-2 py-0.5 text-dashboard-text-muted">
              +{epic.anchor_tags.length - 5}
            </span>
          )}
        </div>
      )}

      {truncatedSummary && (
        <p className="text-sm text-dashboard-text-muted leading-relaxed">
          {truncatedSummary}
        </p>
      )}
    </Link>
  );
}
