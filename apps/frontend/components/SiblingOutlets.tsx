import { getTranslations } from 'next-intl/server';
import { getSiblingOutlets } from '@/lib/queries';
import { getCountryName } from '@/lib/countries';
import SiblingOutletsList from './SiblingOutletsList';

interface Props {
  /** ISO-2 country code to list sources from. */
  countryCode: string | null | undefined;
  /** Outlet to omit from the list (when rendered on an outlet's own page). */
  excludeFeedName?: string;
  /** Cap on number of sources fetched. Default 50 (effectively all for any
   *  country in our corpus). The list component will collapse to the top
   *  ~8 with a "Show all" expander. */
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
  limit = 50,
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
      <SiblingOutletsList outlets={outlets} parentLanguageCode={parentLanguageCode} />
    </div>
  );
}
