import type { Metadata } from 'next';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import { getTranslations } from 'next-intl/server';
export const dynamic = 'force-dynamic';

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('privacy');
  return {
    title: t('title'),
    description: t('metaDescription'),
    alternates: { canonical: '/privacy' },
  };
}

export default async function PrivacyPage() {
  const t = await getTranslations('privacy');
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

          <h3 className="text-xl font-semibold text-dashboard-text mt-6 mb-3">{t('s1aTitle')}</h3>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('s1aText')}
          </p>

          <h3 className="text-xl font-semibold text-dashboard-text mt-6 mb-3">{t('s1bTitle')}</h3>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('s1bText')}
          </p>

          <h3 className="text-xl font-semibold text-dashboard-text mt-6 mb-3">{t('s1cTitle')}</h3>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('s1cIntro')}
          </p>
          <ul className="text-dashboard-text-muted leading-relaxed">
            <li><strong>{t('s1cItem1Label')}</strong> {t('s1cItem1Text')}</li>
            <li><strong>{t('s1cItem2Label')}</strong> {t('s1cItem2Text')}</li>
            <li><strong>{t('s1cItem3Label')}</strong> {t('s1cItem3Text')}</li>
          </ul>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('s1cControl')}
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('s2Title')}</h2>
          <p className="text-dashboard-text-muted leading-relaxed">{t('s2Intro')}</p>
          <ul className="text-dashboard-text-muted leading-relaxed">
            <li>{t('s2Item1')}</li>
            <li>{t('s2Item2')}</li>
            <li>{t('s2Item3')}</li>
            <li>{t('s2Item4')}</li>
            <li>{t('s2Item5')}</li>
          </ul>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('s2NoSell')}
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('s3Title')}</h2>
          <p className="text-dashboard-text-muted leading-relaxed">{t('s3Intro')}</p>
          <ul className="text-dashboard-text-muted leading-relaxed">
            <li><strong>{t('s3Item1Label')}</strong> {t('s3Item1Text')}</li>
            <li><strong>{t('s3Item2Label')}</strong> {t('s3Item2Text')}</li>
            <li><strong>{t('s3Item3Label')}</strong> {t('s3Item3Text')}</li>
          </ul>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('s3Review')}
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('s4Title')}</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('s4Text')}
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('s5Title')}</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('s5Intro')}
          </p>
          <ul className="text-dashboard-text-muted leading-relaxed">
            <li><strong>{t('s5Item1Label')}</strong> {t('s5Item1Text')}</li>
            <li><strong>{t('s5Item2Label')}</strong> {t('s5Item2Text')}</li>
            <li><strong>{t('s5Item3Label')}</strong> {t('s5Item3Text')}</li>
            <li><strong>{t('s5Item4Label')}</strong> {t('s5Item4Text')}</li>
            <li><strong>{t('s5Item5Label')}</strong> {t('s5Item5Text')}</li>
          </ul>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('s5Exercise')}
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
            {t('s10Text')}{' '}
            <a href="mailto:contact@worldbrief.org" className="text-blue-400 hover:underline">
              contact@worldbrief.org
            </a>.
          </p>

          <div className="mt-12 pt-8 border-t border-dashboard-border">
            <p className="text-sm text-dashboard-text-muted">
              {t('seeAlso')} <Link href="/terms" className="text-blue-400 hover:underline">{tFooter('terms')}</Link>
            </p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
