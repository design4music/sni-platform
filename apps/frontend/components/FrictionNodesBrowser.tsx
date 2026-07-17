'use client';

import { useState } from 'react';
import Link from 'next/link';
import type { FnByRegion } from '@/lib/friction-nodes';

interface Props {
  data: FnByRegion[];
  locale: string;
}

export default function FrictionNodesBrowser({ data, locale }: Props) {
  const isDe = locale === 'de';
  const [expandedTheaters, setExpandedTheaters] = useState<Set<string>>(
    new Set(data.flatMap((r) => r.theaters.map((t) => t.id)))
  );

  const toggleTheater = (theaterId: string) => {
    const next = new Set(expandedTheaters);
    if (next.has(theaterId)) {
      next.delete(theaterId);
    } else {
      next.add(theaterId);
    }
    setExpandedTheaters(next);
  };

  const formatDate = (dateStr: string | null): string => {
    if (!dateStr) return isDe ? 'unbekannt' : 'unknown';
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return isDe ? 'heute' : 'today';
    if (diffDays === 1) return isDe ? 'gestern' : 'yesterday';
    if (diffDays < 7) return isDe ? `vor ${diffDays} Tagen` : `${diffDays} days ago`;
    if (diffDays < 30) {
      const weeks = Math.floor(diffDays / 7);
      return isDe ? `vor ${weeks}w` : `${weeks}w ago`;
    }
    if (diffDays < 365) {
      const months = Math.floor(diffDays / 30);
      return isDe ? `vor ${months}m` : `${months}m ago`;
    }
    const years = Math.floor(diffDays / 365);
    return isDe ? `vor ${years} Jahren` : `${years}y ago`;
  };

  const isDormant = (dateStr: string | null): boolean => {
    if (!dateStr) return true;
    const date = new Date(dateStr);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    return diffDays > 90;
  };

  return (
    <div className="space-y-8">
      {data.map((region) => (
        <section key={region.region}>
          <div className="mb-4 flex items-center gap-2">
            <h2 className="text-lg font-semibold text-dashboard-text">
              {region.region}
            </h2>
            <span className="text-xs text-dashboard-text-muted">
              {region.theaters.length} {isDe ? 'Zone(n)' : 'zone(s)'}
            </span>
          </div>

          <div className="space-y-3">
            {region.theaters.map((theater) => (
              <div key={theater.id} className="border border-dashboard-border rounded-lg overflow-hidden">
                {/* Standalone atomic: no members to expand, link straight to it */}
                {theater.standalone ? (
                  <Link
                    href={`/${locale}/friction-nodes/${theater.id}`}
                    className="block px-4 py-3 bg-dashboard-card hover:bg-dashboard-card-hover transition"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-dashboard-text">
                            {theater.name}
                          </span>
                          <span className="text-xs px-2 py-0.5 rounded bg-dashboard-border text-dashboard-text-muted">
                            {theater.event_count} {isDe ? 'Ereignisse' : 'events'}
                          </span>
                          {isDormant(theater.last_activity_date) && (
                            <span className="text-xs px-2 py-0.5 rounded bg-slate-700/30 text-slate-300">
                              {isDe ? 'Ruhend' : 'Dormant'}
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-dashboard-text-muted">
                          {isDe ? 'Zuletzt aktiv' : 'Last active'}: {formatDate(theater.last_activity_date)}
                        </div>
                      </div>
                      <span className="text-dashboard-text-muted text-lg shrink-0">→</span>
                    </div>
                  </Link>
                ) : (
                <>
                {/* Theater header */}
                <button
                  onClick={() => toggleTheater(theater.id)}
                  className="w-full px-4 py-3 bg-dashboard-card hover:bg-dashboard-card-hover transition flex items-center justify-between text-left"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-dashboard-text">
                        {theater.name}
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded bg-dashboard-border text-dashboard-text-muted">
                        {theater.event_count} {isDe ? 'Ereignisse' : 'events'}
                      </span>
                      {isDormant(theater.last_activity_date) && (
                        <span className="text-xs px-2 py-0.5 rounded bg-slate-700/30 text-slate-300">
                          {isDe ? 'Ruhend' : 'Dormant'}
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-dashboard-text-muted">
                      {isDe ? 'Zuletzt aktiv' : 'Last active'}: {formatDate(theater.last_activity_date)}
                    </div>
                  </div>
                  <span
                    className={`ml-2 shrink-0 text-dashboard-text-muted transition-transform ${
                      expandedTheaters.has(theater.id) ? 'rotate-180' : ''
                    }`}
                  >
                    ▼
                  </span>
                </button>

                {/* Atomic FNs list */}
                {expandedTheaters.has(theater.id) && (
                  <div className="bg-dashboard-bg-darker border-t border-dashboard-border divide-y divide-dashboard-border">
                    {theater.members.length === 0 ? (
                      <div className="px-4 py-2 text-xs text-dashboard-text-muted">
                        {isDe ? 'Keine Konflikte in dieser Zone' : 'No conflicts in this zone'}
                      </div>
                    ) : (
                      theater.members.map((member) => (
                        <Link
                          key={member.id}
                          href={`/${locale}/friction-nodes/${member.id}`}
                          className="block px-4 py-3 hover:bg-dashboard-card transition"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <div className="text-sm text-dashboard-text font-medium mb-0.5">
                                {member.name}
                              </div>
                              <div className="flex items-center gap-2 text-xs text-dashboard-text-muted">
                                <span>{member.event_count} {isDe ? 'Ereignisse' : 'events'}</span>
                                <span>•</span>
                                <span>{formatDate(member.last_activity_date)}</span>
                                {isDormant(member.last_activity_date) && (
                                  <>
                                    <span>•</span>
                                    <span className="text-slate-400">
                                      {isDe ? 'Ruhend' : 'Dormant'}
                                    </span>
                                  </>
                                )}
                              </div>
                            </div>
                            <span className="text-dashboard-text-muted text-lg shrink-0">→</span>
                          </div>
                        </Link>
                      ))
                    )}
                  </div>
                )}
                </>
                )}
              </div>
            ))}
          </div>
        </section>
      ))}

      {data.length === 0 && (
        <div className="text-center py-12 text-dashboard-text-muted">
          {isDe ? 'Keine Konfliktzonen verfügbar' : 'No conflict zones available'}
        </div>
      )}
    </div>
  );
}
