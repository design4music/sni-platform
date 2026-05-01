import { Suspense } from 'react';
import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import DashboardLayout from '@/components/DashboardLayout';
import GeoBriefSection from '@/components/GeoBriefSection';
import CentroidMiniMapWrapper from '@/components/CentroidMiniMapWrapper';
import CentroidNarrativeSection from '@/components/narratives/CentroidNarrativeSection';
import { getCentroidById } from '@/lib/queries';
import { REGIONS, getCentroidLabel } from '@/lib/types';
import { buildPageMetadata, breadcrumbList, truncateDescription, type Locale as SeoLocale } from '@/lib/seo';
import JsonLd from '@/components/JsonLd';
import { getTranslations, getLocale } from 'next-intl/server';

// Static reference page — Background Brief, Strategic Narratives, mini-map.
// Content barely changes (curated profile_json + curated narratives), so cache
// for a week. Heavy reads land on cached server output, not the DB.
export const revalidate = 604800;

interface AboutPageProps {
  params: Promise<{ centroid_key: string }>;
}

export async function generateMetadata({ params }: AboutPageProps): Promise<Metadata> {
  const { centroid_key } = await params;
  const locale = (await getLocale()) as SeoLocale;
  const t = await getTranslations('centroid');
  const tCentroids = await getTranslations('centroids');

  const centroid = await getCentroidById(centroid_key, locale);
  if (!centroid) return { title: t('notFound') };
  const label = getCentroidLabel(centroid.id, centroid.label, tCentroids);

  const title = locale === 'de'
    ? `Über ${label} — strategisches Profil`
    : `About ${label} — strategic profile`;

  // Description preference order:
  //   1. profile_json.tldr (curated one-liner if present)
  //   2. centroid.description (general blurb)
  //   3. mechanical fallback
  const profile = centroid.profile_json as { tldr?: string } | null;
  const tldr = profile?.tldr?.trim();
  const fallback = locale === 'de'
    ? `Hintergrundbriefing über ${label}: strategische Konstanten, aktuelle Spannungen, kuratierte geopolitische Narrative.`
    : `Background brief on ${label}: strategic constants, current pressures, and the curated geopolitical narratives covering this country.`;
  const description = truncateDescription(tldr || centroid.description?.trim() || fallback);

  return buildPageMetadata({
    title,
    description,
    path: `/c/${centroid_key}/about`,
    locale,
    ogType: 'article',
  });
}

export default async function CentroidAboutPage({ params }: AboutPageProps) {
  const { centroid_key } = await params;
  const locale = await getLocale();
  const t = await getTranslations('centroid');
  const tCentroids = await getTranslations('centroids');

  const centroid = await getCentroidById(centroid_key, locale);
  if (!centroid) notFound();

  const label = getCentroidLabel(centroid.id, centroid.label, tCentroids);
  const theaterLabel = centroid.primary_theater
    ? (REGIONS as Record<string, string>)[centroid.primary_theater] || centroid.primary_theater
    : null;

  // Breadcrumb: Region › Country › About
  const crumbs: Array<{ name: string; path: string }> = [];
  if (theaterLabel) {
    crumbs.push({ name: theaterLabel, path: `/region/${centroid.primary_theater}` });
  }
  crumbs.push({ name: label, path: `/c/${centroid.id}` });
  crumbs.push({ name: locale === 'de' ? 'Über' : 'About', path: `/c/${centroid.id}/about` });

  const breadcrumb = (
    <div className="text-sm text-dashboard-text-muted flex flex-wrap items-baseline gap-y-0.5 overflow-hidden">
      {theaterLabel && (
        <>
          <Link href={`/region/${centroid.primary_theater}`} className="text-blue-400 hover:text-blue-300 shrink-0">
            {theaterLabel}
          </Link>
          <span className="mx-1 md:mx-2 shrink-0">/</span>
        </>
      )}
      <Link href={`/c/${centroid.id}`} className="text-blue-400 hover:text-blue-300 shrink-0">
        {label}
      </Link>
      <span className="mx-1 md:mx-2 shrink-0">/</span>
      <span>{locale === 'de' ? 'Über' : 'About'}</span>
    </div>
  );

  return (
    <DashboardLayout title={`${locale === 'de' ? 'Über' : 'About'} ${label}`} breadcrumb={breadcrumb}>
      <JsonLd data={breadcrumbList(crumbs)} />

      <div className="space-y-8">
        {/* Background Brief — curated profile_json (strategic constants,
            current pressures, etc). When profile_json absent, just shows
            the mini-map alone. */}
        {centroid.profile_json ? (
          <GeoBriefSection
            profile={centroid.profile_json}
            updatedAt={centroid.updated_at}
            centroidLabel={label}
            miniMap={centroid.iso_codes && centroid.iso_codes.length > 0
              ? <CentroidMiniMapWrapper isoCodes={centroid.iso_codes} />
              : undefined}
          />
        ) : (
          centroid.iso_codes && centroid.iso_codes.length > 0 && (
            <CentroidMiniMapWrapper isoCodes={centroid.iso_codes} />
          )
        )}

        {/* Strategic Narratives — curated geopolitical claims linked to this
            country. Content doesn't vary by month. */}
        <Suspense fallback={null}>
          <CentroidNarrativeSection centroidId={centroid.id} locale={locale} />
        </Suspense>

        {/* Back to monthly */}
        <div className="pt-6 border-t border-dashboard-border">
          <Link
            href={`/c/${centroid.id}`}
            className="inline-flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300 transition"
          >
            ← {label} ({locale === 'de' ? 'aktueller Monat' : 'current month'})
          </Link>
        </div>
      </div>
    </DashboardLayout>
  );
}
