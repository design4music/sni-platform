import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';

export const metadata: Metadata = {
  title: 'Known Issues',
  description: 'Transparency page: known limitations of WorldBrief, why they occur, and current status.',
  alternates: { canonical: '/known-issues' },
};

function Issue({ title, what, why, status }: { title: string; what: string; why: string; status: string }) {
  return (
    <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-6">
      <h3 className="text-xl font-semibold text-dashboard-text mb-4">{title}</h3>
      <p className="text-dashboard-text-muted leading-relaxed mb-2">
        <strong className="text-dashboard-text">What you might see:</strong> {what}
      </p>
      <p className="text-dashboard-text-muted leading-relaxed mb-2">
        <strong className="text-dashboard-text">Why it happens:</strong> {why}
      </p>
      <p className="text-dashboard-text-muted leading-relaxed">
        <strong className="text-dashboard-text">Status:</strong> {status}
      </p>
    </div>
  );
}

export default function KnownIssuesPage() {
  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">Known Issues</h1>
        <div className="prose prose-invert prose-lg max-w-none space-y-6">
          <p className="text-dashboard-text-muted leading-relaxed">
            WorldBrief is an automated system. Some limitations are inherent to the approach. This page describes them honestly so readers know what to expect.
          </p>

          <Issue
            title="Duplicate or near-identical events"
            what="The same story appears as two separate events with slightly different titles."
            why="Clustering groups headlines by shared signals. When headlines use different names or angles for the same story, they can end up in separate clusters."
            status="Automated deduplication catches most cases. Remaining duplicates are a known trade-off of the clustering approach."
          />

          <Issue
            title="Oversized event clusters"
            what='A single event contains headlines about multiple unrelated stories (e.g., "Trump administration" absorbing everything).'
            why="High-frequency signals (prominent person names, major organizations) act as magnets, pulling unrelated headlines into one cluster. Most common for dominant-coverage countries."
            status="Outlier filtering removes off-topic headlines before summarization. The underlying clustering continues to be refined."
          />

          <Issue
            title="Outdated titles or roles in summaries"
            what='A summary says "Former President" when the person is the current president, or uses an outdated title.'
            why="The AI model's training data has a knowledge cutoff. It applies roles it learned during training. Post-processing corrects known cases but cannot catch every person."
            status="Automated corrections are in place for the most prominent cases. Others are caught over time."
          />

          <Issue
            title="Uneven geographic coverage"
            what="Some countries have dozens of events per month, others have very few."
            why="Depends on available English-language and multilingual sources for each region. Western and major-power coverage is naturally denser."
            status="Source list is actively expanded. Coverage will always reflect source availability rather than geopolitical importance."
          />

          <Issue
            title="Summary factual errors"
            what="A summary states something not supported by the underlying headlines, or merges details from unrelated headlines."
            why="The AI generates summaries from headline clusters, not full articles. Ambiguous or contradictory headlines in the same cluster can produce incorrect inferences."
            status="Prompt engineering reduces this. Source links are always provided so readers can verify against original reporting."
          />

          <Issue
            title="Stale monthly digests"
            what="A country or theme page summary doesn't mention a recent development."
            why="Monthly digests regenerate periodically (every 6 hours) with a cooldown. Events that appear between cycles aren't reflected until the next regeneration."
            status="By design -- balances freshness against compute cost. Individual events update faster than monthly digests."
          />

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
