import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';
import { searchAll } from '@/lib/queries';
import { SearchResult } from '@/lib/types';
import Link from 'next/link';

export const dynamic = 'force-dynamic';

interface SearchPageProps {
  searchParams: Promise<{ q?: string }>;
}

export async function generateMetadata({ searchParams }: SearchPageProps): Promise<Metadata> {
  const { q } = await searchParams;
  return {
    title: q ? `Search: ${q}` : 'Search',
  };
}

function resultHref(r: SearchResult): string {
  if (r.type === 'event') return `/events/${r.id}`;
  if (r.type === 'epic') return `/epics/${r.slug}`;
  return `/c/${r.id}`;
}

function TypeBadge({ type }: { type: SearchResult['type'] }) {
  const colors = {
    event: 'bg-blue-500/10 border-blue-500/30 text-blue-400',
    centroid: 'bg-green-500/10 border-green-500/30 text-green-400',
    epic: 'bg-purple-500/10 border-purple-500/30 text-purple-400',
  };
  const labels = { event: 'Topic', centroid: 'Country', epic: 'Epic' };
  return (
    <span className={`inline-flex px-2 py-0.5 rounded-full border text-xs font-medium ${colors[type]}`}>
      {labels[type]}
    </span>
  );
}

export default async function SearchPage({ searchParams }: SearchPageProps) {
  const { q } = await searchParams;
  const query = q?.trim() || '';
  let results: SearchResult[] = [];
  let error = '';

  if (query) {
    try {
      results = await searchAll(query);
    } catch {
      error = 'Search failed. Try simpler terms or remove special characters.';
    }
  }

  return (
    <DashboardLayout
      title="Search"
      breadcrumb={
        <Link href="/" className="text-blue-400 hover:text-blue-300 text-sm">
          &larr; Back
        </Link>
      }
    >
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Search input */}
        <form action="/search" method="GET">
          <div className="relative">
            <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dashboard-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              name="q"
              defaultValue={query}
              placeholder="Search topics, countries, epics..."
              autoFocus
              className="w-full pl-12 pr-4 py-3 bg-dashboard-surface border border-dashboard-border rounded-lg text-dashboard-text placeholder-dashboard-text-muted focus:outline-none focus:border-blue-500 transition"
            />
          </div>
        </form>

        {/* Error state */}
        {error && (
          <p className="text-red-400 text-sm">{error}</p>
        )}

        {/* Results */}
        {query && !error && (
          <div>
            <p className="text-sm text-dashboard-text-muted mb-4">
              {results.length === 0 ? 'No results found' : `${results.length} results`} for &ldquo;{query}&rdquo;
            </p>

            <div className="space-y-3">
              {results.map(r => (
                <Link
                  key={`${r.type}-${r.id}`}
                  href={resultHref(r)}
                  className="block p-4 bg-dashboard-surface border border-dashboard-border rounded-lg hover:border-blue-500 transition"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <TypeBadge type={r.type} />
                    {r.centroid_label && (
                      <span className="text-xs text-dashboard-text-muted">{r.centroid_label}</span>
                    )}
                    {r.date && (
                      <span className="text-xs text-dashboard-text-muted">{r.date}</span>
                    )}
                    {r.sources && (
                      <span className="text-xs text-dashboard-text-muted">{r.sources} sources</span>
                    )}
                  </div>
                  <h3 className="font-semibold text-dashboard-text mb-1">{r.title}</h3>
                  {r.snippet && (
                    <p className="text-sm text-dashboard-text-muted line-clamp-2">{r.snippet}</p>
                  )}
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Empty state (no query) */}
        {!query && (
          <div className="text-center py-12">
            <svg className="w-12 h-12 text-dashboard-text-muted mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <p className="text-dashboard-text-muted">
              Search across topics, countries, and epics
            </p>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
