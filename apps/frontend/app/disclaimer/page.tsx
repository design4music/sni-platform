import DashboardLayout from '@/components/DashboardLayout';

export const dynamic = 'force-dynamic';

export default function DisclaimerPage() {
  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">Disclaimer</h1>

        <div className="prose prose-invert prose-lg max-w-none space-y-6">
          <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-6 mb-8">
            <p className="text-yellow-200 font-medium">
              Important: Lorem ipsum dolor sit amet, consectetur adipiscing elit.
            </p>
          </div>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">AI-Generated Content</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
            incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud
            exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">No Warranty</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu
            fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
            culpa qui officia deserunt mollit anim id est laborum.
          </p>
          <p className="text-dashboard-text-muted leading-relaxed">
            Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque
            laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi
            architecto beatae vitae dicta sunt explicabo.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">Limitation of Liability</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia
            consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. Neque porro
            quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">Use at Your Own Risk</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam,
            nisi ut aliquid ex ea commodi consequatur? Quis autem vel eum iure reprehenderit qui in
            ea voluptate velit esse quam nihil molestiae consequatur, vel illum qui dolorem eum
            fugiat quo voluptas nulla pariatur?
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">Changes to This Disclaimer</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium
            voluptatum deleniti atque corrupti quos dolores et quas molestias excepturi sint
            occaecati cupiditate non provident.
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
