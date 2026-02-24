import DashboardLayout from '@/components/DashboardLayout';

export default function Loading() {
  return (
    <DashboardLayout>
      <div className="space-y-6 animate-pulse">
        <div className="h-5 w-72 bg-dashboard-border/50 rounded" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-40 bg-dashboard-surface border border-dashboard-border rounded-lg p-5">
              <div className="h-5 w-32 bg-dashboard-border rounded mb-3" />
              <div className="h-4 w-48 bg-dashboard-border/50 rounded mb-2" />
              <div className="h-4 w-36 bg-dashboard-border/50 rounded" />
            </div>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
