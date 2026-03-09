import type { Metadata } from 'next';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import { getTranslations } from 'next-intl/server';
export const revalidate = 86400;

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('terms');
  return {
    title: t('title'),
    description: t('metaDescription'),
    alternates: { canonical: '/terms' },
  };
}

export default async function TermsPage() {
  const t = await getTranslations('terms');
  const tFooter = await getTranslations('footer');
  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">{t('title')}</h1>
        <div className="prose prose-invert prose-lg max-w-none space-y-6">
          <p className="text-sm text-dashboard-text-muted italic">{t('lastUpdated')}</p>

          <p className="text-dashboard-text-muted leading-relaxed">
            {t('intro')}
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('s1Title')}</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('s1Text')}
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('s2Title')}</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('s2Text')}
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('s3Title')}</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('s3Text')}
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('s4Title')}</h2>
          <p className="text-dashboard-text-muted leading-relaxed">{t('s4Intro')}</p>
          <ul className="text-dashboard-text-muted leading-relaxed">
            <li>{t('s4Item1')}</li>
            <li>{t('s4Item2')}</li>
            <li>{t('s4Item3')}</li>
            <li>{t('s4Item4')}</li>
            <li>{t('s4Item5')}</li>
          </ul>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('s5Title')}</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('s5Text1')}
          </p>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('s5Text2')}
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('s6Title')}</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('s6Text')}
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('s7Title')}</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('s7Text')}
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('s8Title')}</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('s8Text')}
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('s9Title')}</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('s9Text')}
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('s10Title')}</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('s10Text')}
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('s11Title')}</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('s11Text')}
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('s12Title')}</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('s12Text')}{' '}
            <a href="mailto:contact@worldbrief.org" className="text-blue-400 hover:underline">
              contact@worldbrief.org
            </a>.
          </p>

          <div className="mt-12 pt-8 border-t border-dashboard-border">
            <p className="text-sm text-dashboard-text-muted">
              {t('seeAlso')} <Link href="/privacy" className="text-blue-400 hover:underline">{tFooter('privacy')}</Link>
            </p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
