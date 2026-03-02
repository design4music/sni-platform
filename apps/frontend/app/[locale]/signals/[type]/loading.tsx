import DashboardLayout from '@/components/DashboardLayout';

export default function Loading() {
  return (
    <DashboardLayout>
      <div className="animate-pulse">
        {/* Breadcrumb */}
        <div className="h-4 w-32 bg-dashboard-border/50 rounded mb-4" />

        {/* Header */}
        <div className="h-10 w-56 bg-dashboard-border rounded mb-6" />

        {/* Signal list */}
        <div className="space-y-3">
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3 p-3 bg-dashboard-surface border border-dashboard-border rounded-lg">
              <div className="h-4 w-32 bg-dashboard-border rounded" />
              <div className="h-3 w-20 bg-dashboard-border/50 rounded ml-auto" />
            </div>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
