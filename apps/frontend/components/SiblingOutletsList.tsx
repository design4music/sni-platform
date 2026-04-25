'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useTranslations } from 'next-intl';
import type { SiblingOutlet } from '@/lib/queries';
import { generateSlug } from '@/lib/slug';
import PublisherFavicon from './PublisherFavicon';

const DEFAULT_VISIBLE = 8;

interface Props {
  outlets: SiblingOutlet[];
  parentLanguageCode?: string | null;
}

/**
 * Renders the sibling-outlet list with a "Show all (N)" expander when there
 * are more rows than DEFAULT_VISIBLE. Server parent (SiblingOutlets) is in
 * charge of fetching + the heading; this client child just owns the
 * collapsed/expanded state.
 */
export default function SiblingOutletsList({ outlets, parentLanguageCode }: Props) {
  const t = useTranslations('sources');
  const [expanded, setExpanded] = useState(false);
  const total = outlets.length;
  const visible = expanded ? outlets : outlets.slice(0, DEFAULT_VISIBLE);
  const remaining = total - DEFAULT_VISIBLE;

  return (
    <>
      <ul className="space-y-1">
        {visible.map(o => (
          <li key={o.feed_name}>
            <Link
              href={`/sources/${o.slug || generateSlug(o.feed_name)}`}
              className="flex items-center gap-2 px-2 py-1.5 -mx-2 rounded text-sm text-dashboard-text-muted hover:text-dashboard-text hover:bg-dashboard-border/30 transition min-w-0"
            >
              <PublisherFavicon
                publisher={o.feed_name}
                domain={o.source_domain}
                size={20}
              />
              <span className="truncate flex-1">{o.feed_name}</span>
              {o.language_code && o.language_code !== parentLanguageCode && (
                <span className="uppercase text-[10px] tabular-nums text-dashboard-text-muted/70 flex-shrink-0">
                  {o.language_code}
                </span>
              )}
            </Link>
          </li>
        ))}
      </ul>
      {!expanded && remaining > 0 && (
        <button
          onClick={() => setExpanded(true)}
          className="mt-2 text-xs text-blue-400 hover:text-blue-300 transition"
        >
          {t('showAllSources', { count: remaining })}
        </button>
      )}
      {expanded && total > DEFAULT_VISIBLE && (
        <button
          onClick={() => setExpanded(false)}
          className="mt-2 text-xs text-blue-400 hover:text-blue-300 transition"
        >
          {t('showFewerSources')}
        </button>
      )}
    </>
  );
}
