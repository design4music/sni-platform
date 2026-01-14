import DashboardLayout from '@/components/DashboardLayout';

export const dynamic = 'force-dynamic';

export default function AboutPage() {
  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">About WorldBrief</h1>

        <div className="prose prose-invert prose-lg max-w-none space-y-6">
          <p className="text-lg text-dashboard-text-muted leading-relaxed">
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor
            incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud
            exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">Our Mission</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu
            fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
            culpa qui officia deserunt mollit anim id est laborum.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">How It Works</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque
            laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi
            architecto beatae vitae dicta sunt explicabo.
          </p>
          <p className="text-dashboard-text-muted leading-relaxed">
            Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia
            consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">Our Approach</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci
            velit, sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam
            aliquam quaerat voluptatem.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">Contact</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam,
            nisi ut aliquid ex ea commodi consequatur? Quis autem vel eum iure reprehenderit qui in
            ea voluptate velit esse quam nihil molestiae consequatur.
          </p>
        </div>
      </div>
    </DashboardLayout>
  );
}
