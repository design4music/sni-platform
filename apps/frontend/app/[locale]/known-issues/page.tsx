import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';
import { buildAlternates } from '@/lib/seo';
import { getTranslations } from 'next-intl/server';
export const revalidate = 86400;

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('knownIssues');
  return {
    title: t('title'),
    description: t('metaDescription'),
    alternates: buildAlternates('/known-issues'),
  };
}

function Issue({ title, what, why, status, whatLabel, whyLabel, statusLabel }: {
  title: string; what: string; why: string; status: string;
  whatLabel: string; whyLabel: string; statusLabel: string;
}) {
  return (
    <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-6">
      <h3 className="text-xl font-semibold text-dashboard-text mb-4">{title}</h3>
      <p className="text-dashboard-text-muted leading-relaxed mb-2">
        <strong className="text-dashboard-text">{whatLabel}</strong> {what}
      </p>
      <p className="text-dashboard-text-muted leading-relaxed mb-2">
        <strong className="text-dashboard-text">{whyLabel}</strong> {why}
      </p>
      <p className="text-dashboard-text-muted leading-relaxed">
        <strong className="text-dashboard-text">{statusLabel}</strong> {status}
      </p>
    </div>
  );
}

export default async function KnownIssuesPage() {
  const t = await getTranslations('knownIssues');
  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">{t('title')}</h1>
        <div className="prose prose-invert prose-lg max-w-none space-y-6">
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('intro')}
          </p>

          <Issue
            title={t('issue1Title')}
            what={t('issue1What')}
            why={t('issue1Why')}
            status={t('issue1Status')}
            whatLabel={t('whatYouMightSee')}
            whyLabel={t('whyItHappens')}
            statusLabel={t('status')}
          />

          <Issue
            title={t('issue2Title')}
            what={t('issue2What')}
            why={t('issue2Why')}
            status={t('issue2Status')}
            whatLabel={t('whatYouMightSee')}
            whyLabel={t('whyItHappens')}
            statusLabel={t('status')}
          />

          <Issue
            title={t('issue3Title')}
            what={t('issue3What')}
            why={t('issue3Why')}
            status={t('issue3Status')}
            whatLabel={t('whatYouMightSee')}
            whyLabel={t('whyItHappens')}
            statusLabel={t('status')}
          />

          <Issue
            title={t('issue4Title')}
            what={t('issue4What')}
            why={t('issue4Why')}
            status={t('issue4Status')}
            whatLabel={t('whatYouMightSee')}
            whyLabel={t('whyItHappens')}
            statusLabel={t('status')}
          />

          <Issue
            title={t('issue5Title')}
            what={t('issue5What')}
            why={t('issue5Why')}
            status={t('issue5Status')}
            whatLabel={t('whatYouMightSee')}
            whyLabel={t('whyItHappens')}
            statusLabel={t('status')}
          />

          <Issue
            title={t('issue6Title')}
            what={t('issue6What')}
            why={t('issue6Why')}
            status={t('issue6Status')}
            whatLabel={t('whatYouMightSee')}
            whyLabel={t('whyItHappens')}
            statusLabel={t('status')}
          />

          <div className="mt-12 pt-8 border-t border-dashboard-border">
            <p className="text-sm text-dashboard-text-muted italic">
              {t('lastUpdated')}
            </p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
