import DashboardLayout from '@/components/DashboardLayout';

export default function Loading() {
  return (
    <DashboardLayout>
      <div className="space-y-8 animate-pulse">
        <div>
          <div className="h-8 w-48 bg-dashboard-border rounded mb-4" />
          <div className="h-5 w-96 bg-dashboard-border/50 rounded" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-32 bg-dashboard-surface border border-dashboard-border rounded-lg p-5">
              <div className="h-5 w-32 bg-dashboard-border rounded mb-3" />
              <div className="h-4 w-48 bg-dashboard-border/50 rounded" />
            </div>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
