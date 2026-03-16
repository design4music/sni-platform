import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import ComparativeContent from '@/components/ComparativeContent';
import { query } from '@/lib/db';
import { setRequestLocale, getTranslations } from 'next-intl/server';
import { auth } from '@/auth';
import type { EntityAnalysis } from '@/lib/queries';

export const dynamic = 'force-dynamic';

interface Props {
  params: Promise<{ locale: string; id: string }>;
}

async function getUserAnalysis(id: string, userId: string, locale?: string): Promise<(EntityAnalysis & { input_text: string | null; title: string | null }) | null> {
  const rows = await query<EntityAnalysis & { input_text: string | null; title: string | null }>(
    `SELECT id, entity_type, entity_id, cluster_count,
            ${locale === 'de' ? 'COALESCE(sections_de, sections)' : 'sections'} as sections,
            scores,
            ${locale === 'de' ? 'COALESCE(synthesis_de, synthesis)' : 'synthesis'} as synthesis,
            ${locale === 'de' ? 'COALESCE(blind_spots_de, blind_spots)' : 'blind_spots'} as blind_spots,
            ${locale === 'de' ? 'COALESCE(conflicts_de, conflicts)' : 'conflicts'} as conflicts,
            created_at::text,
            input_text, title
     FROM entity_analyses
     WHERE entity_id = $1 AND entity_type = 'user_input' AND user_id = $2`,
    [id, userId]
  );
  return rows.length > 0 ? rows[0] : null;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  return {
    title: `Analysis - WorldBrief`,
    description: 'RAI analysis of user-submitted text',
  };
}

export default async function UserAnalysisPage({ params }: Props) {
  const { locale, id } = await params;
  setRequestLocale(locale);

  const session = await auth();
  if (!session?.user?.id) return notFound();

  const analysis = await getUserAnalysis(id, session.user.id, locale);
  if (!analysis) return notFound();

  const t = await getTranslations('comparative');

  const breadcrumb = (
    <div className="text-sm text-dashboard-text-muted">
      <Link href="/profile" className="text-blue-400 hover:text-blue-300">
        Profile
      </Link>
      <span className="mx-2">/</span>
      <span>Analysis</span>
    </div>
  );

  return (
    <DashboardLayout breadcrumb={breadcrumb}>
      {/* LLM disclaimer */}
      <div className="mb-6 p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
        <p className="text-xs text-amber-300 leading-relaxed">
          {t('llmDisclaimer')}
        </p>
      </div>

      {/* Title */}
      <h1 className="text-3xl md:text-4xl font-bold mb-2">
        RAI Analysis
      </h1>
      {analysis.title && (
        <p className="text-lg text-dashboard-text-muted mb-4 line-clamp-2">
          {analysis.title}
        </p>
      )}

      {/* Original input */}
      {analysis.input_text && (
        <details className="mb-6 bg-dashboard-surface border border-dashboard-border rounded-lg">
          <summary className="px-4 py-3 text-sm text-dashboard-text-muted cursor-pointer hover:text-dashboard-text transition">
            Original input
          </summary>
          <div className="px-4 pb-4">
            <p className="text-sm text-dashboard-text-muted whitespace-pre-wrap">{analysis.input_text}</p>
          </div>
        </details>
      )}

      {/* Analysis content (reuses ComparativeContent rendering) */}
      <ComparativeContent
        entityType="user_input"
        entityId={id}
        cachedAnalysis={analysis}
        locale={locale}
      />
    </DashboardLayout>
  );
}
