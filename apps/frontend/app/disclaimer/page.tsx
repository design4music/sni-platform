import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';

export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: 'Method & Disclaimer',
  description: 'How WorldBrief works: automated ingestion, multilingual processing, and structured synthesis of global news. Limitations and editorial policy.',
  alternates: { canonical: '/disclaimer' },
};

export default function DisclaimerPage() {
  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">Method & Disclaimer</h1>
        <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">How WorldBrief works</h2>
        <div className="prose prose-invert prose-lg max-w-none space-y-6">
          <p className="text-dashboard-text-muted leading-relaxed">
            WorldBrief is an automated system designed to organize large volumes of global reporting into structured, readable briefings.</p>
          <p className="text-dashboard-text-muted leading-relaxed">
            The system continuously ingests reporting from a curated, multilingual set of international media and strategic communication channels. Incoming material is processed, categorized, and synthesized into thematic briefings organized by geography and topic.</p>
          <p className="text-dashboard-text-muted leading-relaxed">
            Automation is used to handle scale and speed; structure is used to preserve meaning.</p>
          <p className="text-dashboard-text-muted leading-relaxed">
            The result is a navigable overview of ongoing developments across regions and issue areas, updated on a rolling basis.</p>
        </div>
        <div className="prose prose-invert prose-lg max-w-none space-y-6">
          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">What is automated</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            WorldBrief relies on machine-assisted processes to:
          </p>
          <ul className="text-dashboard-text-muted leading-relaxed">
            <li>ingest and normalize reporting from diverse sources,</li>
            <li>detect recurring topics and patterns of coverage,</li>
            <li>generate compressed summaries reflecting the content of aggregated reporting.</li>
          </ul>
          <p className="text-dashboard-text-muted leading-relaxed">
            Automation enables breadth and timeliness that would be impractical to achieve manually.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">What is deliberate</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            While processing is automated, <strong>the system itself is not accidental</strong>.
          </p>
          <p className="text-dashboard-text-muted leading-relaxed">
            Key aspects of WorldBrief are shaped by explicit design decisions, including:
          </p>
          <ul className="text-dashboard-text-muted leading-relaxed">
            <li>how information is grouped and labeled,</li>
            <li>how geographic and thematic scopes are defined,</li>
            <li>how summaries are structured and presented,</li>
            <li>and which trade-offs are accepted in favor of clarity and orientation.</li>
          </ul>
          <p className="text-dashboard-text-muted leading-relaxed">
            The current system reflects extensive experimentation, multiple abandoned approaches, and nearly a year of iterative development. Many alternative designs were tested and discarded in the process.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">Limitations</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            WorldBrief is designed for orientation, not completeness.
          </p>
          <p className="text-dashboard-text-muted leading-relaxed">
            As with any large-scale automated system:
          </p>
          <ul className="text-dashboard-text-muted leading-relaxed">
            <li>summaries may omit details that appear in individual articles,</li>
            <li>reporting reflects the biases, priorities, and blind spots of its source material,</li>
            <li>coverage density varies by region and topic,</li>
            <li>updates may lag behind real-time events.</li>
          </ul>
          <p className="text-dashboard-text-muted leading-relaxed">
            WorldBrief should be treated as a starting point for understanding, not a definitive account.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">Responsibility and use</h2>
          <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-6 mb-8">
            <p className="text-yellow-200 font-medium">
              WorldBrief does not make claims of objectivity, neutrality, or authority.
            </p>
            <p className="text-yellow-200 font-medium">
              It does not issue judgments, predictions, or recommendations.
            </p>
            <p className="text-yellow-200 font-medium">
              It does not replace original reporting, expert analysis, or independent verification.
            </p>
            <p className="text-yellow-200 font-medium">
              Users are encouraged to consult primary sources, follow links provided, and apply their own judgment when interpreting the information presented.
            </p>
          </div>
          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">Transparency</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            All content on WorldBrief is generated by automated processes based on aggregated reporting.<br />
            Inclusion of a source does not imply endorsement.
          </p>
          <p className="text-dashboard-text-muted leading-relaxed">
            The project aims to be transparent about its purpose and limitations while preserving the integrity of its methods.
          </p>

          <div className="mt-12 pt-8 border-t border-dashboard-border">
            <p className="text-sm text-dashboard-text-muted italic">
              Last updated: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
            </p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
