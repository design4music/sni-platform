import FlagImg from '@/components/FlagImg';
import type { CentroidLookupEntry } from '@/lib/friction-nodes-shared';

interface Props {
  centroidIds: string[];
  lookup: Map<string, CentroidLookupEntry>;
  size?: 'sm' | 'md';
}

/**
 * Country pills with flag + display label, mirroring OutletStanceSection's
 * identity-pill style. Falls back to the raw centroid_id if not found in
 * the lookup (defensive — should never happen for active centroids).
 */
export default function CoalitionPills({ centroidIds, lookup, size = 'sm' }: Props) {
  const sizeCls =
    size === 'md'
      ? 'px-3 py-1 text-sm gap-2'
      : 'px-2 py-0.5 text-xs gap-1.5';
  const flagSize = size === 'md' ? 16 : 13;

  return (
    <div className="flex flex-wrap gap-1.5">
      {centroidIds.map((cid) => {
        const entry = lookup.get(cid);
        const label = entry?.label ?? cid;
        const iso = entry?.iso2;
        return (
          <span
            key={cid}
            title={cid}
            className={`inline-flex items-center rounded-full border border-dashboard-border bg-dashboard-border/30 text-dashboard-text font-medium ${sizeCls}`}
          >
            {iso ? (
              <FlagImg iso2={iso} size={flagSize} />
            ) : (
              <span
                aria-hidden
                className="inline-block w-3 h-3 rounded-sm bg-dashboard-text-muted/40 shrink-0"
              />
            )}
            <span className="truncate max-w-[14rem]">{label}</span>
          </span>
        );
      })}
    </div>
  );
}
