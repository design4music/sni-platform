import type { Metadata } from 'next';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';

export const metadata: Metadata = {
  title: 'Privacy Policy',
  description: 'WorldBrief Privacy Policy. How we collect, use, and protect your data.',
  alternates: { canonical: '/privacy' },
};

export default function PrivacyPage() {
  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">Privacy Policy</h1>
        <div className="prose prose-invert prose-lg max-w-none space-y-6">
          <p className="text-sm text-dashboard-text-muted italic">Last updated: February 2026</p>

          <p className="text-dashboard-text-muted leading-relaxed">
            This Privacy Policy describes how Maksim Micheliov, operating as WorldBrief (&quot;we&quot;, &quot;us&quot;, &quot;our&quot;), collects, uses, and protects your information when you use our service.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">1. Information We Collect</h2>

          <h3 className="text-xl font-semibold text-dashboard-text mt-6 mb-3">Account Information</h3>
          <p className="text-dashboard-text-muted leading-relaxed">
            When you create an account, we collect your name and email address as provided through our authentication service.
          </p>

          <h3 className="text-xl font-semibold text-dashboard-text mt-6 mb-3">Usage Data</h3>
          <p className="text-dashboard-text-muted leading-relaxed">
            We automatically collect information about how you interact with WorldBrief, including pages visited, features used, time spent on pages, and referring URLs. This data is collected through analytics tools and server logs.
          </p>

          <h3 className="text-xl font-semibold text-dashboard-text mt-6 mb-3">Cookies</h3>
          <p className="text-dashboard-text-muted leading-relaxed">
            WorldBrief uses cookies for:
          </p>
          <ul className="text-dashboard-text-muted leading-relaxed">
            <li><strong>Authentication:</strong> session cookies to keep you signed in,</li>
            <li><strong>Analytics:</strong> cookies set by Google Analytics (GA4) to understand usage patterns,</li>
            <li><strong>Preferences:</strong> cookies to remember your display settings.</li>
          </ul>
          <p className="text-dashboard-text-muted leading-relaxed">
            You can control cookies through your browser settings. Disabling cookies may affect some features.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">2. How We Use Your Information</h2>
          <p className="text-dashboard-text-muted leading-relaxed">We use collected information to:</p>
          <ul className="text-dashboard-text-muted leading-relaxed">
            <li>provide, maintain, and improve the service,</li>
            <li>authenticate your identity and manage your account,</li>
            <li>understand usage patterns and improve the product,</li>
            <li>communicate important updates about the service,</li>
            <li>process payments (when paid features are available).</li>
          </ul>
          <p className="text-dashboard-text-muted leading-relaxed">
            We do not sell your personal information to third parties.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">3. Third-Party Services</h2>
          <p className="text-dashboard-text-muted leading-relaxed">WorldBrief uses the following third-party services that may collect data:</p>
          <ul className="text-dashboard-text-muted leading-relaxed">
            <li><strong>Google Analytics (GA4):</strong> for website analytics and usage tracking,</li>
            <li><strong>NextAuth / Auth.js:</strong> for authentication (Google and GitHub OAuth),</li>
            <li><strong>Stripe:</strong> for payment processing (when paid features are available).</li>
          </ul>
          <p className="text-dashboard-text-muted leading-relaxed">
            Each service operates under its own privacy policy. We encourage you to review them.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">4. Data Retention</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            We retain your account information for as long as your account is active. Usage data is retained in aggregate form for up to 26 months (Google Analytics default). If you delete your account, we will remove your personal information within 30 days, except where retention is required by law.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">5. Your Rights</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            Depending on your jurisdiction, you may have the right to:
          </p>
          <ul className="text-dashboard-text-muted leading-relaxed">
            <li><strong>Access</strong> the personal data we hold about you,</li>
            <li><strong>Correct</strong> inaccurate personal data,</li>
            <li><strong>Delete</strong> your personal data,</li>
            <li><strong>Export</strong> your data in a portable format,</li>
            <li><strong>Object</strong> to or restrict certain processing of your data.</li>
          </ul>
          <p className="text-dashboard-text-muted leading-relaxed">
            To exercise any of these rights, contact us at the email below.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">6. GDPR (European Users)</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            If you are located in the European Economic Area, our legal basis for processing your data is: consent (for analytics cookies), contract performance (for providing the service), and legitimate interest (for improving the service and preventing abuse).
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">7. CCPA (California Users)</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            California residents have the right to know what personal information is collected, request deletion, and opt out of the sale of personal information. WorldBrief does not sell personal information.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">8. Data Security</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            We implement reasonable security measures to protect your information, including encrypted connections (HTTPS), secure authentication, and restricted database access. However, no method of transmission over the internet is 100% secure.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">9. Changes to This Policy</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            We may update this Privacy Policy from time to time. Material changes will be communicated via the service or by email. The &quot;Last updated&quot; date at the top reflects the most recent revision.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">10. Contact</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            For questions about this Privacy Policy or to exercise your data rights, contact us at{' '}
            <a href="mailto:contact@worldbrief.org" className="text-blue-400 hover:underline">
              contact@worldbrief.org
            </a>.
          </p>

          <div className="mt-12 pt-8 border-t border-dashboard-border">
            <p className="text-sm text-dashboard-text-muted">
              See also: <Link href="/terms" className="text-blue-400 hover:underline">Terms of Service</Link>
            </p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
