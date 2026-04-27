import DashboardLayout from '@/components/DashboardLayout';

function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse bg-dashboard-border/50 rounded ${className || ''}`} />;
}

/**
 * Skeleton for the outlet landing page. Renders during SSR so the
 * navigation feels instant — instead of a blank screen while six
 * server queries resolve, the user sees the layout taking shape.
 */
export default function OutletLandingLoading() {
  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 pb-6 border-b border-dashboard-border">
          <Skeleton className="h-4 w-24" />
          <div className="flex items-center gap-4 mt-4">
            <Skeleton className="w-12 h-12 rounded" />
            <div className="space-y-2">
              <Skeleton className="h-9 w-56" />
              <Skeleton className="h-4 w-72" />
            </div>
          </div>
          <Skeleton className="mt-4 h-12 w-full max-w-3xl" />
        </div>

        {/* Editorial stance heatmap */}
        <div className="mb-10">
          <Skeleton className="h-7 w-64 mb-2" />
          <Skeleton className="h-4 w-full max-w-3xl mb-4" />
          <Skeleton className="h-72 w-full rounded-lg" />
        </div>

        {/* Coverage volume chart */}
        <div className="mb-10">
          <Skeleton className="h-7 w-64 mb-2" />
          <Skeleton className="h-4 w-full max-w-3xl mb-4" />
          <Skeleton className="h-80 w-full rounded-lg" />
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 mt-3">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-4 w-full" />
            ))}
          </div>
        </div>

        {/* Topic mix over time */}
        <div className="mb-10">
          <Skeleton className="h-7 w-64 mb-2" />
          <Skeleton className="h-4 w-full max-w-3xl mb-4" />
          <Skeleton className="h-56 w-full rounded-lg" />
        </div>

        {/* Lifetime overview cards */}
        <div className="mb-8">
          <Skeleton className="h-7 w-48 mb-3" />
          <div className="hidden md:grid md:grid-cols-5 gap-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <div
                key={i}
                className="p-3 bg-dashboard-surface border border-dashboard-border rounded-lg space-y-2"
              >
                <Skeleton className="h-5 w-16" />
                <Skeleton className="h-3 w-20" />
              </div>
            ))}
          </div>
          <div className="md:hidden flex gap-2 overflow-x-hidden">
            {Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="flex-shrink-0 min-w-[8.5rem] p-3 bg-dashboard-surface border border-dashboard-border rounded-lg space-y-2"
              >
                <Skeleton className="h-5 w-16" />
                <Skeleton className="h-3 w-20" />
              </div>
            ))}
          </div>
        </div>

        {/* 3-col footer */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          {Array.from({ length: 3 }).map((_, col) => (
            <div key={col} className="space-y-2">
              <Skeleton className="h-4 w-24 mb-3" />
              {Array.from({ length: 7 }).map((_, i) => (
                <Skeleton key={i} className="h-4 w-full" />
              ))}
            </div>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
