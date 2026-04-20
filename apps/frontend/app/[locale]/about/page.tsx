import type { Metadata } from 'next';
import Image from 'next/image';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import { buildAlternates } from '@/lib/seo';
import { getTranslations } from 'next-intl/server';
export const revalidate = 86400;

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('about');
  return {
    title: t('metaTitle'),
    description: t('metaDescription'),
    alternates: buildAlternates('/about'),
  };
}

export default async function AboutPage() {
  const t = await getTranslations('about');
  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">{t('heading')}</h1>
        <div className="prose prose-invert prose-lg max-w-none space-y-6">
          <p className="text-lg text-dashboard-text-muted leading-relaxed">
            {t('intro')}
          </p>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('problem')}
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('howItWorksHeading')}</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('howItWorks1')}
          </p>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('howItWorks2')}
          </p>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('howItWorks3')}{' '}
            <Link href="/methodology" className="text-blue-400 hover:underline">{t('methodologyLink')}</Link>.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('whatIsNotHeading')}</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('whatIsNotIntro')}
          </p>
          <ul className="text-dashboard-text-muted leading-relaxed">
            <li><strong>{t('notOpinion')}</strong> {t('notOpinionDetail')}</li>
            <li><strong>{t('notPrediction')}</strong> {t('notPredictionDetail')}</li>
            <li><strong>{t('notReplacement')}</strong></li>
          </ul>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('verificationNote')}
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">{t('founderHeading')}</h2>
          <div className="float-left mr-6 mb-4 w-[120px] sm:w-[200px]">
            <Image
              src="/maksim.webp"
              alt={t('founderImageAlt')}
              width={200}
              height={200}
              className="rounded-full border-2 border-dashboard-border w-full h-auto"
            />
            <a
              href="https://www.linkedin.com/in/mmdesign/"
              target="_blank"
              rel="noopener noreferrer"
              className="block text-center text-xs text-blue-400 hover:underline mt-2"
            >
              {t('linkedIn')}
            </a>
          </div>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('founderP1')}
          </p>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('founderP2')}
          </p>
          <p className="text-dashboard-text-muted leading-relaxed">
            {t('founderP3')}
          </p>

          <div className="mt-12 pt-8 border-t border-dashboard-border">
            <p className="text-sm text-dashboard-text-muted">
              {t('contactPrompt')}{' '}
              <a href="mailto:contact@worldbrief.org" className="text-blue-400 hover:underline">
                contact@worldbrief.org
              </a>
            </p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
