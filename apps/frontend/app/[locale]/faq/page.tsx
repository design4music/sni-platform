import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';
import { getTranslations } from 'next-intl/server';
export const revalidate = 86400;

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('faq');
  return {
    title: t('metaTitle'),
    description: t('metaDescription'),
    alternates: { canonical: '/faq' },
  };
}

export default async function FAQPage() {
  const t = await getTranslations('faq');
  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">{t('heading')}</h1>
        <div className="prose prose-invert prose-lg max-w-none space-y-6">

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('generalHeading')}</h2>

          <h3 className="text-xl font-semibold text-dashboard-text">{t('q1')}</h3>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('a1')}
          </p>

          <h3 className="text-xl font-semibold text-dashboard-text">{t('q2')}</h3>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('a2')}
          </p>

          <h3 className="text-xl font-semibold text-dashboard-text">{t('q3')}</h3>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('a3')}
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('coverageHeading')}</h2>

          <h3 className="text-xl font-semibold text-dashboard-text">{t('q4')}</h3>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('a4')}
          </p>

          <h3 className="text-xl font-semibold text-dashboard-text">{t('q5')}</h3>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('a5')}
          </p>

          <h3 className="text-xl font-semibold text-dashboard-text">{t('q6')}</h3>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('a6')}
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('featuresHeading')}</h2>

          <h3 className="text-xl font-semibold text-dashboard-text">{t('q7')}</h3>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('a7')}
          </p>

          <h3 className="text-xl font-semibold text-dashboard-text">{t('q8')}</h3>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('a8')}
          </p>

          <h3 className="text-xl font-semibold text-dashboard-text">{t('q9')}</h3>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('a9')}
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('dataHeading')}</h2>

          <h3 className="text-xl font-semibold text-dashboard-text">{t('q10')}</h3>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t.rich('a10', {
              privacyLink: (chunks) => <a href="/privacy" className="text-blue-400 hover:text-blue-300">{chunks}</a>,
            })}
          </p>

          <h3 className="text-xl font-semibold text-dashboard-text">{t('q11')}</h3>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t.rich('a11', {
              termsLink: (chunks) => <a href="/terms" className="text-blue-400 hover:text-blue-300">{chunks}</a>,
            })}
          </p>

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
