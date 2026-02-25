import type { Metadata } from 'next';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';

export const metadata: Metadata = {
  title: 'Pricing',
  description: 'WorldBrief pricing plans. Free access to global news briefings, with Pro features for deeper analysis.',
  alternates: { canonical: '/pricing' },
};

const freeTier = [
  'Browse all country and region pages',
  'Event headlines and source counts',
  'Trending events overview',
  'Basic search',
];

const proTier = [
  'Full AI-generated event summaries',
  'Narrative and framing analysis',
  'Signal tracking (persons, orgs, commodities, policies)',
  'Monthly intelligence digests',
  'Epic story timelines',
  'Priority access to new features',
];

export default function PricingPage() {
  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-4">Pricing</h1>
        <p className="text-lg text-dashboard-text-muted mb-12">
          WorldBrief is preparing for launch. Explore the platform for free, with Pro features coming soon.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Free Tier */}
          <div className="border border-dashboard-border rounded-lg p-8 bg-dashboard-surface">
            <h2 className="text-2xl font-bold mb-2">Free</h2>
            <p className="text-dashboard-text-muted mb-6">Global news briefings at a glance</p>
            <ul className="space-y-3 mb-8">
              {freeTier.map((feature) => (
                <li key={feature} className="flex items-start gap-3 text-dashboard-text-muted">
                  <span className="text-green-400 mt-0.5 shrink-0">--</span>
                  <span>{feature}</span>
                </li>
              ))}
            </ul>
            <Link
              href="/"
              className="block w-full text-center py-3 px-6 rounded-lg border border-dashboard-border text-dashboard-text hover:bg-white/5 transition"
            >
              Browse WorldBrief
            </Link>
          </div>

          {/* Pro Tier */}
          <div className="border border-blue-500/40 rounded-lg p-8 bg-blue-950/20 relative">
            <div className="absolute top-4 right-4 text-xs font-medium bg-blue-500/20 text-blue-300 px-3 py-1 rounded-full">
              Coming Soon
            </div>
            <h2 className="text-2xl font-bold mb-2">Pro</h2>
            <p className="text-dashboard-text-muted mb-6">Deep analysis and intelligence tools</p>
            <ul className="space-y-3 mb-8">
              {proTier.map((feature) => (
                <li key={feature} className="flex items-start gap-3 text-dashboard-text-muted">
                  <span className="text-blue-400 mt-0.5 shrink-0">--</span>
                  <span>{feature}</span>
                </li>
              ))}
            </ul>
            <Link
              href="/auth/signin"
              className="block w-full text-center py-3 px-6 rounded-lg bg-blue-600 text-white hover:bg-blue-500 transition"
            >
              Sign up to get notified
            </Link>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-dashboard-border">
          <p className="text-sm text-dashboard-text-muted text-center">
            Have questions? Reach out at{' '}
            <a href="mailto:contact@worldbrief.org" className="text-blue-400 hover:underline">
              contact@worldbrief.org
            </a>
          </p>
        </div>
      </div>
    </DashboardLayout>
  );
}
