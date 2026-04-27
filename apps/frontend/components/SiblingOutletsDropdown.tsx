'use client';

import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import { useTranslations } from 'next-intl';
import type { SiblingOutlet } from '@/lib/queries';
import { generateSlug } from '@/lib/slug';
import PublisherFavicon from './PublisherFavicon';

interface Props {
  outlets: SiblingOutlet[];
  /** ISO-2 of the parent outlet's country, used in the trigger label
   *  ("X more from {country}"). */
  countryName: string;
  parentLanguageCode?: string | null;
}

/**
 * Compact "More sources from <country>" dropdown for the outlet
 * landing page header. Click-outside and Escape close the popover.
 */
export default function SiblingOutletsDropdown({
  outlets,
  countryName,
  parentLanguageCode,
}: Props) {
  const t = useTranslations('sources');
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDocClick = (e: MouseEvent) => {
      if (!wrapperRef.current) return;
      if (!wrapperRef.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', onDocClick);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDocClick);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  if (outlets.length === 0) return null;

  return (
    <div className="relative inline-block" ref={wrapperRef}>
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        aria-expanded={open}
        aria-haspopup="listbox"
        className="inline-flex items-center gap-1 text-sm text-blue-400 hover:text-blue-300 transition"
      >
        {t('moreFromCountryShort', { count: outlets.length, country: countryName })}
        <svg
          className={`w-3 h-3 transition-transform ${open ? 'rotate-180' : ''}`}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2.5}
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {open && (
        <div
          role="listbox"
          className="absolute right-0 sm:right-auto sm:left-0 top-full mt-2 z-40 w-72 max-w-[calc(100vw-1rem)] max-h-[60vh] overflow-y-auto bg-dashboard-surface border border-dashboard-border rounded-lg shadow-xl p-2"
        >
          <ul className="space-y-0.5">
            {outlets.map(o => (
              <li key={o.feed_name}>
                <Link
                  href={`/sources/${o.slug || generateSlug(o.feed_name)}`}
                  onClick={() => setOpen(false)}
                  className="flex items-center gap-2 px-2 py-1.5 rounded text-sm text-dashboard-text-muted hover:text-dashboard-text hover:bg-dashboard-border/30 transition min-w-0"
                >
                  <PublisherFavicon
                    publisher={o.feed_name}
                    domain={o.source_domain}
                    size={18}
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
        </div>
      )}
    </div>
  );
}
