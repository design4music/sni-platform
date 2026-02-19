'use client';

import { useState, useMemo } from 'react';
import { Title } from '@/lib/types';

interface PublisherGroup {
  publisher: string;
  titles: Title[];
}

function PublisherFavicon({ publisher }: { publisher: string }) {
  // Map known publisher names to domains for favicons
  const domainMap: Record<string, string> = {
    'Reuters': 'reuters.com',
    'AP News': 'apnews.com',
    'BBC': 'bbc.com',
    'Financial Times': 'ft.com',
    'The Wall Street Journal': 'wsj.com',
    'The New York Times': 'nytimes.com',
    'The Washington Post': 'washingtonpost.com',
    'NPR': 'npr.org',
    'The Guardian': 'theguardian.com',
    'CNN': 'cnn.com',
    'Al Jazeera': 'aljazeera.com',
    'Bloomberg': 'bloomberg.com',
    'POLITICO': 'politico.com',
    'Forbes': 'forbes.com',
    'ABC News': 'abcnews.go.com',
    'NBC News': 'nbcnews.com',
    'CBS News': 'cbsnews.com',
    'DW': 'dw.com',
    'France 24': 'france24.com',
    'The Times of Israel': 'timesofisrael.com',
    'South China Morning Post': 'scmp.com',
  };

  const domain = domainMap[publisher];
  if (!domain) {
    return (
      <span className="w-5 h-5 rounded bg-dashboard-border flex items-center justify-center text-[10px] text-dashboard-text-muted flex-shrink-0">
        {publisher.charAt(0).toUpperCase()}
      </span>
    );
  }

  return (
    <img
      src={`https://www.google.com/s2/favicons?domain=${domain}&sz=32`}
      alt=""
      width={20}
      height={20}
      className="rounded flex-shrink-0 opacity-80"
      style={{ filter: 'saturate(0.7) brightness(0.9)' }}
    />
  );
}

function PublisherAccordion({ group, defaultOpen }: { group: PublisherGroup; defaultOpen: boolean }) {
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
                <a
                  href={title.url_gnews}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-dashboard-text hover:text-blue-400 transition"
                >
                  {title.title_display}
                </a>
              ) : (
                <span className="text-sm text-dashboard-text">{title.title_display}</span>
              )}
              <div className="text-xs text-dashboard-text-muted mt-0.5">
                {title.pubdate_utc && (
                  <span>
                    {new Date(title.pubdate_utc).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  </span>
                )}
                {title.detected_language && title.detected_language !== 'en' && (
                  <span className="ml-2 uppercase">{title.detected_language}</span>
                )}
              </div>
            </div>
          ))}
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
        {titles.length} headlines from {groups.length} publishers
      </p>
      <div className="space-y-0.5">
        {visible.map((group, i) => (
          <PublisherAccordion key={group.publisher} group={group} defaultOpen={i === 0} />
        ))}
      </div>
      {!showAll && remaining > 0 && (
        <button
          onClick={() => setShowAll(true)}
          className="mt-3 text-sm text-blue-400 hover:text-blue-300"
        >
          Show {remaining} more publishers
        </button>
      )}
    </div>
  );
}
