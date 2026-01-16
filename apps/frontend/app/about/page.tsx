import DashboardLayout from '@/components/DashboardLayout';

export const dynamic = 'force-dynamic';

export default function AboutPage() {
  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">About WorldBrief</h1>
        <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">Why WorldBrief Exists</h2>
        <div className="prose prose-invert prose-lg max-w-none space-y-6">
          <p className="text-lg text-dashboard-text-muted leading-relaxed">
            The volume of global reporting has never been higher, yet understanding has not kept pace. News is fragmented across regions, languages, and platforms, while attention is pulled toward speed, novelty, and outrage.
          </p>
          <p className="text-dashboard-text-muted leading-relaxed">As a result, it has become increasingly difficult to answer basic questions:</p>
          <ul className="text-dashboard-text-muted leading-relaxed">
            <li>What is actually happening?</li>
            <li>Where is it happening?</li>
            <li>How do different issues connect across regions and topics?</li>
          </ul>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">What WorldBrief does</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            WorldBrief organizes global reporting into continuously updated briefings structured by geography and theme.
          </p>
          <p className="text-dashboard-text-muted leading-relaxed">Instead of presenting isolated articles or endless feeds, the system:</p>
          <ul className="text-dashboard-text-muted leading-relaxed">
            <li>aggregates reporting from diverse international sources,</li>
            <li>compresses coverage into coherent summaries,</li>
            <li>and allows exploration by map, topic, and time.</li>
          </ul>
          <p className="text-dashboard-text-muted leading-relaxed">The goal is not to replace reading, but to provide orientation: a clear starting point for understanding what matters and where to look deeper.</p>
          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">What WorldBrief is not</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            WorldBrief is intentionally limited in scope. It is:
          </p>
          <ul className="text-dashboard-text-muted leading-relaxed">
            <li><strong>not an opinion outlet</strong> and does not promote a political position,</li>
            <li><strong>not a prediction engine</strong> and does not forecast outcomes,</li>
            <li><strong>not a replacement for original journalism.</strong></li>
          </ul>
          <p className="text-dashboard-text-muted leading-relaxed">
            All summaries are derived from existing reporting, and source links are provided to enable independent verification and further reading.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">About the author</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            WorldBrief is developed by an independent researcher and product builder with a long-standing interest in global affairs, information systems, and analytical adequacy.
          </p>
          <p className="text-dashboard-text-muted leading-relaxed">The project is driven less by commentary than by method: how information is structured, contextualized, and presented in order to support better judgment in complex environments.</p>
          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">Support</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            WorldBrief is an independent project, developed and maintained outside of large institutions.
          </p>
          <p className="text-dashboard-text-muted leading-relaxed">
            If you find it useful and would like to support its continued development, you can do so here. Support is entirely optional and helps cover infrastructure, data access, and ongoing refinement.
          </p>
        </div>
      </div>
    </DashboardLayout>
  );
}
