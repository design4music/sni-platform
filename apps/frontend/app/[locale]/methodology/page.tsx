import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';
import { getTranslations } from 'next-intl/server';
export const revalidate = 86400;

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('methodology');
  return {
    title: t('title'),
    description: t('metaDescription'),
    alternates: { canonical: '/methodology' },
  };
}

export default async function MethodologyPage() {
  const t = await getTranslations('methodology');
  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">{t('heading')}</h1>
        <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('howItWorksHeading')}</h2>
        <div className="prose prose-invert prose-lg max-w-none space-y-6">
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('howItWorks1')}</p>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('howItWorks2')}</p>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('howItWorks3')}</p>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('howItWorks4')}</p>
        </div>
        <div className="prose prose-invert prose-lg max-w-none space-y-6">
          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('automatedHeading')}</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('automatedIntro')}
          </p>
          <ul className="text-dashboard-text-muted leading-relaxed">
            <li>{t('automatedItem1')}</li>
            <li>{t('automatedItem2')}</li>
            <li>{t('automatedItem3')}</li>
          </ul>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('automatedOutro')}
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('deliberateHeading')}</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('deliberateIntro')}<strong>{t('deliberateIntroStrong')}</strong>.
          </p>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('deliberateDesign')}
          </p>
          <ul className="text-dashboard-text-muted leading-relaxed">
            <li>{t('deliberateItem1')}</li>
            <li>{t('deliberateItem2')}</li>
            <li>{t('deliberateItem3')}</li>
            <li>{t('deliberateItem4')}</li>
          </ul>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('deliberateOutro')}
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('limitationsHeading')}</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('limitationsIntro')}
          </p>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('limitationsNote')}
          </p>
          <ul className="text-dashboard-text-muted leading-relaxed">
            <li>{t('limitationsItem1')}</li>
            <li>{t('limitationsItem2')}</li>
            <li>{t('limitationsItem3')}</li>
            <li>{t('limitationsItem4')}</li>
          </ul>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('limitationsOutro')}
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('responsibilityHeading')}</h2>
          <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-6 mb-8">
            <p className="text-yellow-200 font-medium">
              {t('responsibilityLine1')}
            </p>
            <p className="text-yellow-200 font-medium">
              {t('responsibilityLine2')}
            </p>
            <p className="text-yellow-200 font-medium">
              {t('responsibilityLine3')}
            </p>
            <p className="text-yellow-200 font-medium">
              {t('responsibilityLine4')}
            </p>
          </div>
          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('transparencyHeading')}</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('transparencyLine1')}<br />
            {t('transparencyLine2')}
          </p>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('transparencyLine3')}
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
