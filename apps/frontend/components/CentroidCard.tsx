import Link from 'next/link';
import { Centroid } from '@/lib/types';

interface CentroidCardProps {
  centroid: Centroid;
  showClass?: boolean;
}

export default function CentroidCard({ centroid, showClass = false }: CentroidCardProps) {
  return (
    <Link
      href={`/c/${centroid.id}`}
      className="block p-6 border border-dashboard-border bg-dashboard-surface rounded-lg hover:border-blue-500 transition"
    >
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold mb-2">{centroid.label}</h3>
          {showClass && (
            <span className="text-xs px-2 py-1 rounded bg-dashboard-border text-dashboard-text-muted">
              {centroid.class === 'geo' ? 'Geographic' : 'Systemic'}
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}
