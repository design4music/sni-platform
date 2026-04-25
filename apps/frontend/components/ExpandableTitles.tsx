'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import { useTranslations, useLocale } from 'next-intl';
import { Title } from '@/lib/types';
import { generateSlug as slugify } from '@/lib/slug';
import ExternalLink from './ExternalLink';
import PublisherFaviconShared from './PublisherFavicon';

// Re-export the shared favicon under the historical name so existing
// imports continue to work. The implementation now lives in
// components/PublisherFavicon.tsx (no 'use client' so it's reusable in
// server components like SiblingOutlets).
export const PublisherFavicon = PublisherFaviconShared;

interface PublisherGroup {
  publisher: string;
  titles: Title[];
}

function PublisherAccordion({ group, defaultOpen, dateFmtLocale }: { group: PublisherGroup; defaultOpen: boolean; dateFmtLocale: string }) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="mb-1">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3 py-2.5 rounded-lg bg-dashboard-border/30 hover:bg-dashboard-border/50 transition-colors"
        aria-expanded={isOpen}
      >
        <span className="flex items-center gap-2.5 text-left min-w-0">
          <PublisherFavicon publisher={group.publisher} />
          <span className="font-medium text-sm text-dashboard-text truncate">
            {group.publisher}
          </span>
        </span>
        <span className="flex items-center gap-2 flex-shrink-0">
          <span className="text-xs text-dashboard-text-muted">
            {group.titles.length}
          </span>
          <span className={`text-dashboard-text-muted transition-transform duration-200 text-xs ${isOpen ? 'rotate-90' : ''}`}>
            &#9656;
          </span>
        </span>
      </button>

      {isOpen && (
        <div className="mt-1 ml-7 space-y-1 pb-1">
          {group.titles.map(title => (
            <div key={title.id} className="py-1.5">
              {title.url_gnews ? (
                <ExternalLink href={title.url_gnews} className="text-sm text-dashboard-text hover:text-blue-400 transition">
                  {title.title_display}
                </ExternalLink>
              ) : (
                <span className="text-sm text-dashboard-text">{title.title_display}</span>
              )}
              <div className="text-xs text-dashboard-text-muted mt-0.5">
                {title.pubdate_utc && (
                  <span>
                    {new Date(title.pubdate_utc).toLocaleDateString(dateFmtLocale, { month: 'short', day: 'numeric' })}
                  </span>
                )}
                {title.detected_language && title.detected_language !== 'en' && (
                  <span className="ml-2 uppercase">{title.detected_language}</span>
                )}
              </div>
            </div>
          ))}
          <div className="pt-2">
            <Link
              href={`/sources/${slugify(group.publisher)}`}
              className="text-xs text-blue-400 hover:text-blue-300 transition"
            >
              {group.publisher} &rarr;
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

interface ExpandableTitlesProps {
  titles: Title[];
  initialCount?: number;
}

export default function ExpandableTitles({ titles, initialCount = 10 }: ExpandableTitlesProps) {
  const [showAll, setShowAll] = useState(false);
  const t = useTranslations('event');
  const locale = useLocale();
  const dateFmtLocale = locale === 'de' ? 'de-DE' : 'en-US';

  const groups = useMemo(() => {
    const map = new Map<string, Title[]>();
    for (const t of titles) {
      const pub = t.publisher_name || 'Unknown';
      if (!map.has(pub)) map.set(pub, []);
      map.get(pub)!.push(t);
    }
    return Array.from(map.entries())
      .map(([publisher, titles]) => ({ publisher, titles }))
      .sort((a, b) => b.titles.length - a.titles.length);
  }, [titles]);

  const visible = showAll ? groups : groups.slice(0, initialCount);
  const remaining = groups.length - initialCount;

  return (
    <div>
      <p className="text-sm text-dashboard-text-muted mb-3">
        {t('headlinesFrom', { headlines: titles.length, publishers: groups.length })}
      </p>
      <div className="space-y-0.5">
        {visible.map((group, i) => (
          <PublisherAccordion key={group.publisher} group={group} defaultOpen={i === 0} dateFmtLocale={dateFmtLocale} />
        ))}
      </div>
      {!showAll && remaining > 0 && (
        <button
          onClick={() => setShowAll(true)}
          className="mt-3 text-sm text-blue-400 hover:text-blue-300"
        >
          {t('showMorePublishers', { count: remaining })}
        </button>
      )}
    </div>
  );
}
