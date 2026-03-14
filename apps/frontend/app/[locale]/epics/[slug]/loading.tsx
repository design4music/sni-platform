import DashboardLayout from '@/components/DashboardLayout';

export default function Loading() {
  const sidebar = (
    <div className="animate-pulse lg:sticky lg:top-24 space-y-6">
      <div className="hidden lg:block space-y-2">
        <div className="h-5 w-32 bg-dashboard-border rounded" />
        <div className="h-8 w-full bg-dashboard-border/50 rounded" />
        <div className="h-8 w-full bg-dashboard-border/50 rounded" />
        <div className="h-8 w-full bg-dashboard-border/50 rounded" />
      </div>
      <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4 space-y-3">
        <div className="h-4 w-24 bg-dashboard-border rounded" />
        <div className="flex flex-wrap gap-1.5">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-6 w-16 bg-dashboard-border/50 rounded" />
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <DashboardLayout sidebar={sidebar}>
      <div className="animate-pulse">
        {/* Header */}
        <div className="mb-8 pb-8 border-b border-dashboard-border">
          <div className="h-10 w-3/4 bg-dashboard-border rounded mb-2" />
          <div className="h-4 w-64 bg-dashboard-border/50 rounded mb-4" />
          <div className="h-4 w-full bg-dashboard-border/50 rounded mb-2" />
          <div className="h-4 w-5/6 bg-dashboard-border/50 rounded mb-4" />
          <div className="flex gap-1.5">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-5 w-20 bg-dashboard-border/50 rounded" />
            ))}
          </div>
        </div>

        {/* Timeline */}
        <div className="mb-8 pb-8 border-b border-dashboard-border">
          <div className="h-7 w-48 bg-dashboard-border rounded mb-4" />
          <div className="space-y-3">
            <div className="h-4 w-full bg-dashboard-border/50 rounded" />
            <div className="h-4 w-5/6 bg-dashboard-border/50 rounded" />
            <div className="h-4 w-4/6 bg-dashboard-border/50 rounded" />
            <div className="h-4 w-full bg-dashboard-border/50 rounded" />
            <div className="h-4 w-3/4 bg-dashboard-border/50 rounded" />
          </div>
        </div>

        {/* Coverage by Country */}
        <div className="mb-8 pb-8 border-b border-dashboard-border">
          <div className="h-7 w-56 bg-dashboard-border rounded mb-4" />
          <div className="space-y-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-14 w-full bg-dashboard-border/30 rounded-lg" />
            ))}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
