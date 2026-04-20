import type { Metadata } from 'next';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import { buildAlternates } from '@/lib/seo';
import { getTranslations } from 'next-intl/server';
export const revalidate = 86400;

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('pricingPage');
  return {
    title: t('title'),
    description: t('metaDescription'),
    alternates: buildAlternates('/pricing'),
  };
}

const freeFeatureKeys = ['freeFeature1', 'freeFeature2', 'freeFeature3', 'freeFeature4'] as const;
const proFeatureKeys = ['proFeature1', 'proFeature2', 'proFeature3', 'proFeature4', 'proFeature5', 'proFeature6'] as const;

export default async function PricingPage() {
  const t = await getTranslations('pricingPage');
  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-4">{t('heading')}</h1>
        <p className="text-lg text-dashboard-text-muted mb-12">
          {t('subtitle')}
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Free Tier */}
          <div className="border border-dashboard-border rounded-lg p-8 bg-dashboard-surface">
            <h2 className="text-2xl font-bold mb-2">{t('freeName')}</h2>
            <p className="text-dashboard-text-muted mb-6">{t('freeTagline')}</p>
            <ul className="space-y-3 mb-8">
              {freeFeatureKeys.map((key) => (
                <li key={key} className="flex items-start gap-3 text-dashboard-text-muted">
                  <span className="text-green-400 mt-0.5 shrink-0">--</span>
                  <span>{t(key)}</span>
                </li>
              ))}
            </ul>
            <Link
              href="/"
              className="block w-full text-center py-3 px-6 rounded-lg border border-dashboard-border text-dashboard-text hover:bg-white/5 transition"
            >
              {t('freeCta')}
            </Link>
          </div>

          {/* Pro Tier */}
          <div className="border border-blue-500/40 rounded-lg p-8 bg-blue-950/20 relative">
            <div className="absolute top-4 right-4 text-xs font-medium bg-blue-500/20 text-blue-300 px-3 py-1 rounded-full">
              {t('comingSoon')}
            </div>
            <h2 className="text-2xl font-bold mb-2">{t('proName')}</h2>
            <p className="text-dashboard-text-muted mb-6">{t('proTagline')}</p>
            <ul className="space-y-3 mb-8">
              {proFeatureKeys.map((key) => (
                <li key={key} className="flex items-start gap-3 text-dashboard-text-muted">
                  <span className="text-blue-400 mt-0.5 shrink-0">--</span>
                  <span>{t(key)}</span>
                </li>
              ))}
            </ul>
            <Link
              href="/auth/signin"
              className="block w-full text-center py-3 px-6 rounded-lg bg-blue-600 text-white hover:bg-blue-500 transition"
            >
              {t('proCta')}
            </Link>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-dashboard-border">
          <p className="text-sm text-dashboard-text-muted text-center">
            {t('contactPrompt')}{' '}
            <a href="mailto:contact@worldbrief.org" className="text-blue-400 hover:underline">
              contact@worldbrief.org
            </a>
          </p>
        </div>
      </div>
    </DashboardLayout>
  );
}
