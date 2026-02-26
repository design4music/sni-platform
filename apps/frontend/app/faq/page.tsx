import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';

export const metadata: Metadata = {
  title: 'FAQ',
  description: 'Frequently asked questions about WorldBrief: coverage, sources, features, pricing, and data privacy.',
  alternates: { canonical: '/faq' },
};

export default function FAQPage() {
  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">Frequently Asked Questions</h1>
        <div className="prose prose-invert prose-lg max-w-none space-y-6">

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">General</h2>

          <h3 className="text-xl font-semibold text-dashboard-text">What is WorldBrief?</h3>
          <p className="text-dashboard-text-muted leading-relaxed">
            WorldBrief is an automated news intelligence platform. It continuously ingests reporting from 210+ sources across 60+ countries, clusters related headlines into events, and generates structured briefings organized by geography and theme.
          </p>

          <h3 className="text-xl font-semibold text-dashboard-text">How is this different from Google News?</h3>
          <p className="text-dashboard-text-muted leading-relaxed">
            Google News aggregates and personalizes articles for individual readers. WorldBrief does something different: it synthesizes reporting into structured briefings organized by country, region, and theme. Headlines are clustered into events using AI, not ranked by engagement. There is no algorithmic personalization -- everyone sees the same picture.
          </p>

          <h3 className="text-xl font-semibold text-dashboard-text">How fresh is the data?</h3>
          <p className="text-dashboard-text-muted leading-relaxed">
            Ingestion runs continuously. Event clustering and summaries regenerate every 6 hours. Individual events may update faster than monthly digests.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">Coverage</h2>

          <h3 className="text-xl font-semibold text-dashboard-text">How many sources does WorldBrief track?</h3>
          <p className="text-dashboard-text-muted leading-relaxed">
            Over 210 sources across 60+ countries in 20+ languages. The source list includes major international outlets, regional media, and specialized publications.
          </p>

          <h3 className="text-xl font-semibold text-dashboard-text">Why is coverage uneven across countries?</h3>
          <p className="text-dashboard-text-muted leading-relaxed">
            Coverage depends on available sources. English-language and Western media are overrepresented in the global information ecosystem, and this is reflected in WorldBrief. The source list is actively expanded to improve geographic balance.
          </p>

          <h3 className="text-xl font-semibold text-dashboard-text">What languages are supported?</h3>
          <p className="text-dashboard-text-muted leading-relaxed">
            WorldBrief ingests reporting in 20+ languages. All output -- summaries, event descriptions, and briefings -- is presented in English.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">Features & Pricing</h2>

          <h3 className="text-xl font-semibold text-dashboard-text">What&apos;s free?</h3>
          <p className="text-dashboard-text-muted leading-relaxed">
            Browsing countries, regions, trending topics, headlines, and source links is free and does not require an account.
          </p>

          <h3 className="text-xl font-semibold text-dashboard-text">What will Pro include?</h3>
          <p className="text-dashboard-text-muted leading-relaxed">
            Pro will unlock full event summaries, narrative analysis, signal tracking, and email digests.
          </p>

          <h3 className="text-xl font-semibold text-dashboard-text">When will Pro launch?</h3>
          <p className="text-dashboard-text-muted leading-relaxed">
            Coming soon. Sign up to be notified when Pro becomes available.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">Data & Privacy</h2>

          <h3 className="text-xl font-semibold text-dashboard-text">Does WorldBrief store my data?</h3>
          <p className="text-dashboard-text-muted leading-relaxed">
            Minimal data is stored: account information if you sign in, and standard analytics via GA4. See the <a href="/privacy" className="text-blue-400 hover:text-blue-300">Privacy Policy</a> for full details.
          </p>

          <h3 className="text-xl font-semibold text-dashboard-text">Can I use WorldBrief content in my work?</h3>
          <p className="text-dashboard-text-muted leading-relaxed">
            Summaries are AI-generated from publicly available reporting. You may reference them with a link back to WorldBrief. See the <a href="/terms" className="text-blue-400 hover:text-blue-300">Terms of Service</a> for the full usage policy.
          </p>

          <div className="mt-12 pt-8 border-t border-dashboard-border">
            <p className="text-sm text-dashboard-text-muted italic">
              Last updated: February 2026
            </p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
