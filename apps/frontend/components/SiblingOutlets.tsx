import Link from 'next/link';
import { getTranslations } from 'next-intl/server';
import { getSiblingOutlets } from '@/lib/queries';
import { getCountryName } from '@/lib/countries';
import PublisherFavicon from './PublisherFavicon';

interface Props {
  /** ISO-2 country code to list sources from. */
  countryCode: string | null | undefined;
  /** Outlet to omit from the list (when rendered on an outlet's own page). */
  excludeFeedName?: string;
  /** Cap on number of sources rendered. Default 12. */
  limit?: number;
  /**
   * Optional language code of the parent context. When set, sibling outlets
   * whose language differs will show a small lang tag. (Without this, every
   * outlet shows its lang — visually noisy on a list of monolingual peers.)
   */
  parentLanguageCode?: string | null;
}

/**
 * Autonomous "sources from <country>" sidebar block.
 *
 * Self-fetches via getSiblingOutlets. Hides itself entirely when:
 *   - countryCode is missing
 *   - the country has no other active outlets
 *
 * Heading is "More sources from X" when an excludeFeedName is set (we're
 * on that outlet's own profile), else "Sources from X" (centroid pages,
 * etc.).
 */
export default async function SiblingOutlets({
  countryCode,
  excludeFeedName,
  limit = 12,
  parentLanguageCode,
}: Props) {
  if (!countryCode) return null;

  const outlets = await getSiblingOutlets(
    countryCode,
    excludeFeedName ?? '',
    limit
  );
  if (outlets.length === 0) return null;

  const t = await getTranslations('sources');
  const countryName = getCountryName(countryCode) || countryCode;
  const heading = excludeFeedName
    ? t('moreFromCountry', { country: countryName })
    : t('sourcesFromCountry', { country: countryName });

  return (
    <div>
      <h3 className="text-sm font-medium text-dashboard-text-muted mb-2">
        {heading}
      </h3>
      <ul className="space-y-1">
        {outlets.map(o => (
          <li key={o.feed_name}>
            <Link
              href={`/sources/${encodeURIComponent(o.feed_name)}`}
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
    </div>
  );
}
