import DashboardLayout from '@/components/DashboardLayout';

export default function Loading() {
  return (
    <DashboardLayout>
      <div className="animate-pulse">
        {/* Header */}
        <div className="mb-8 pb-6 border-b border-dashboard-border">
          <div className="h-10 w-48 bg-dashboard-border rounded mb-2" />
          <div className="h-5 w-24 bg-dashboard-border/50 rounded" />
        </div>

        {/* Timeline placeholder */}
        <div className="h-40 bg-dashboard-surface border border-dashboard-border rounded-lg mb-8" />

        {/* Relationship highlights grid */}
        <div className="p-4 rounded-lg border border-dashboard-border bg-dashboard-surface mb-8">
          <div className="h-4 w-48 bg-dashboard-border rounded mb-4" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="space-y-2">
                <div className="flex items-center gap-2">
                  <div className="h-4 w-16 bg-dashboard-border/50 rounded" />
                  <div className="h-4 w-28 bg-dashboard-border rounded" />
                </div>
                <div className="h-4 w-full bg-dashboard-border/50 rounded" />
                <div className="h-3 w-4/5 bg-dashboard-border/30 rounded" />
              </div>
            ))}
          </div>
        </div>

        {/* Geo + Tracks row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="h-48 bg-dashboard-surface border border-dashboard-border rounded-lg" />
          <div className="h-48 bg-dashboard-surface border border-dashboard-border rounded-lg" />
        </div>
      </div>
    </DashboardLayout>
  );
}
