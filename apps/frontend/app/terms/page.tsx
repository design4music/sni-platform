import type { Metadata } from 'next';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';

export const metadata: Metadata = {
  title: 'Terms of Service',
  description: 'WorldBrief Terms of Service. Rules and conditions governing use of the platform.',
  alternates: { canonical: '/terms' },
};

export default function TermsPage() {
  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">Terms of Service</h1>
        <div className="prose prose-invert prose-lg max-w-none space-y-6">
          <p className="text-sm text-dashboard-text-muted italic">Last updated: February 2026</p>

          <p className="text-dashboard-text-muted leading-relaxed">
            These Terms of Service (&quot;Terms&quot;) govern your use of WorldBrief, operated by Maksim Micheliov, operating as WorldBrief (&quot;we&quot;, &quot;us&quot;, &quot;our&quot;). By accessing or using WorldBrief, you agree to be bound by these Terms.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">1. Description of Service</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            WorldBrief is an automated global news intelligence platform that aggregates, processes, and synthesizes reporting from international media sources into structured briefings. The service includes country and region pages, event summaries, thematic tracking, narrative analysis, and related features.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">2. Acceptance of Terms</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            By creating an account or using WorldBrief, you confirm that you are at least 16 years old and agree to comply with these Terms. If you do not agree, you must stop using the service.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">3. User Accounts</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            Some features require an account. You are responsible for maintaining the confidentiality of your login credentials and for all activity under your account. You agree to provide accurate information and to notify us promptly if you suspect unauthorized access.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">4. Acceptable Use</h2>
          <p className="text-dashboard-text-muted leading-relaxed">You agree not to:</p>
          <ul className="text-dashboard-text-muted leading-relaxed">
            <li>use the service for any unlawful purpose,</li>
            <li>scrape, crawl, or systematically extract data from WorldBrief without permission,</li>
            <li>attempt to gain unauthorized access to any part of the service,</li>
            <li>interfere with or disrupt the service or its infrastructure,</li>
            <li>redistribute WorldBrief content commercially without authorization.</li>
          </ul>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">5. Intellectual Property</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            WorldBrief content -- including AI-generated summaries, analysis, site design, and code -- is the property of Maksim Micheliov unless otherwise noted. Summaries are original works derived from publicly available reporting. Source articles remain the property of their respective publishers.
          </p>
          <p className="text-dashboard-text-muted leading-relaxed">
            You may share individual briefings for personal, non-commercial use with attribution. Bulk reproduction or commercial use requires written permission.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">6. Paid Services</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            WorldBrief may offer paid subscription plans. Payment terms, pricing, and refund policies will be presented at the time of purchase. We reserve the right to change pricing with reasonable notice.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">7. Disclaimer of Warranties</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            WorldBrief is provided &quot;AS IS&quot; and &quot;AS AVAILABLE&quot; without warranties of any kind, whether express or implied. We do not guarantee that the service will be uninterrupted, error-free, or that content will be complete or accurate. WorldBrief is a tool for orientation, not a definitive source of truth.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">8. Limitation of Liability</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            To the maximum extent permitted by applicable law, Maksim Micheliov and WorldBrief shall not be liable for any indirect, incidental, special, consequential, or punitive damages arising from your use of the service. Our total liability shall not exceed the amount you have paid us in the 12 months preceding the claim.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">9. Changes to Terms</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            We may update these Terms from time to time. Material changes will be communicated via the service or by email. Continued use after changes take effect constitutes acceptance of the revised Terms.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">10. Termination</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            We may suspend or terminate your access to WorldBrief at our discretion if you violate these Terms. You may delete your account at any time by contacting us.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">11. Governing Law</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            These Terms shall be governed by and construed in accordance with the laws of the jurisdiction in which the operator resides, without regard to conflict of law principles.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">12. Contact</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            For questions about these Terms, contact us at{' '}
            <a href="mailto:contact@worldbrief.org" className="text-blue-400 hover:underline">
              contact@worldbrief.org
            </a>.
          </p>

          <div className="mt-12 pt-8 border-t border-dashboard-border">
            <p className="text-sm text-dashboard-text-muted">
              See also: <Link href="/privacy" className="text-blue-400 hover:underline">Privacy Policy</Link>
            </p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
