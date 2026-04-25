import DashboardLayout from '@/components/DashboardLayout';

function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse bg-dashboard-border/50 rounded ${className || ''}`} />;
}

export default function OutletLoading() {
  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8 pb-8 border-b border-dashboard-border">
          <Skeleton className="h-4 w-24 mb-4" />
          <div className="flex items-center gap-4 mt-4">
            <Skeleton className="w-12 h-12 rounded" />
            <div>
              <Skeleton className="h-8 w-56 mb-2" />
              <Skeleton className="h-4 w-40" />
            </div>
          </div>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 mb-8">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="p-3 bg-dashboard-surface border border-dashboard-border rounded-lg">
              <Skeleton className="h-6 w-12 mb-1" />
              <Skeleton className="h-3 w-20" />
            </div>
          ))}
        </div>

        {/* Track bar */}
        <Skeleton className="h-7 w-full rounded-full mb-8" />

        {/* Map placeholder */}
        <Skeleton className="h-[500px] w-full rounded-lg mb-10" />

        {/* Two columns */}
        <div className="grid md:grid-cols-2 gap-6 mb-10">
          <div className="space-y-2">
            <Skeleton className="h-4 w-24 mb-3" />
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-4 w-full" />
            ))}
          </div>
          <div className="space-y-2">
            <Skeleton className="h-4 w-24 mb-3" />
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-4 w-full" />
            ))}
          </div>
        </div>

        {/* Topics grid */}
        <Skeleton className="h-6 w-32 mb-4" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full rounded-lg" />
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
