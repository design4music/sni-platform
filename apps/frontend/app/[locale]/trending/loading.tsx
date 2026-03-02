import DashboardLayout from '@/components/DashboardLayout';

export default function Loading() {
  return (
    <DashboardLayout>
      <div className="space-y-8 animate-pulse">
        <div>
          <div className="h-10 w-64 bg-dashboard-border rounded mb-2" />
          <div className="h-5 w-96 bg-dashboard-border rounded" />
        </div>

        {/* Hero skeleton - full width */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-56 bg-dashboard-surface border border-dashboard-border rounded-lg" />
          ))}
        </div>

        {/* Two-column skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-20 bg-dashboard-surface border border-dashboard-border rounded-lg" />
            ))}
          </div>
          <div className="space-y-6">
            <div className="h-6 w-40 bg-dashboard-border rounded" />
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="space-y-2">
                <div className="h-3 w-28 bg-dashboard-border rounded" />
                {Array.from({ length: 5 }).map((_, j) => (
                  <div key={j} className="flex justify-between">
                    <div className="h-4 w-32 bg-dashboard-border rounded" />
                    <div className="h-4 w-14 bg-dashboard-border rounded" />
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
