'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useTranslations, useLocale } from 'next-intl';

interface MonthNavProps {
  months: string[];       // YYYY-MM sorted descending
  currentMonth: string;
  baseUrl: string;        // e.g. /c/AMERICAS-USA/t/geo_politics
}

function formatMonth(month: string, locale: string): string {
  const [year, m] = month.split('-');
  const date = new Date(parseInt(year), parseInt(m, 10) - 1);
  return date.toLocaleDateString(locale === 'de' ? 'de-DE' : 'en-US', { month: 'short', year: 'numeric' });
}

export default function MonthNav({ months, currentMonth, baseUrl }: MonthNavProps) {
  const t = useTranslations('nav');
  const locale = useLocale();
  const [archiveOpen, setArchiveOpen] = useState(false);

  if (months.length === 0) return null;

  // Current and previous are the two most recent months
  const latest = months[0];
  const previous = months.length > 1 ? months[1] : null;
  const archive = months.slice(2);

  const pill = (month: string) => {
    const isActive = month === currentMonth;
    if (isActive) {
      return (
        <span
          key={month}
          className="px-3 py-1.5 rounded-md text-sm font-medium bg-blue-500 text-white cursor-default"
        >
          {formatMonth(month, locale)}
        </span>
      );
    }
    return (
      <Link
        key={month}
        href={`${baseUrl}?month=${month}`}
        className="px-3 py-1.5 rounded-md text-sm font-medium transition-colors bg-dashboard-surface border border-dashboard-border text-dashboard-text-muted hover:text-dashboard-text hover:border-blue-500/50"
      >
        {formatMonth(month, locale)}
      </Link>
    );
  };

  return (
    <div>
      <h3 className="text-lg font-semibold mb-3 text-dashboard-text">{t('viewByMonth')}</h3>
      <div className="flex gap-2 mb-2">
        {pill(latest)}
        {previous && pill(previous)}
      </div>

      {archive.length > 0 && (
        <div className="rounded-lg bg-dashboard-surface border border-dashboard-border overflow-hidden mt-2">
          <button
            onClick={() => setArchiveOpen(!archiveOpen)}
            className="w-full flex items-center justify-between px-4 py-2.5 text-sm font-medium text-dashboard-text-muted hover:text-dashboard-text hover:bg-dashboard-border/50 transition"
          >
            <span>{t('previousMonthsArchive')}</span>
            <svg
              className={`w-4 h-4 transition-transform ${archiveOpen ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {archiveOpen && (
            <div className="border-t border-dashboard-border">
              {archive.map(m => {
                const isActive = m === currentMonth;
                return (
                  <Link
                    key={m}
                    href={`${baseUrl}?month=${m}`}
                    className={`block px-6 py-2.5 text-sm transition ${
                      isActive
                        ? 'bg-blue-600/20 text-blue-400 font-medium'
                        : 'text-dashboard-text-muted hover:text-dashboard-text hover:bg-dashboard-border'
                    }`}
                  >
                    {formatMonth(m, locale)}
                  </Link>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
