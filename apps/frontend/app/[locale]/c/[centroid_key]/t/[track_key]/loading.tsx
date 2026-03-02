import DashboardLayout from '@/components/DashboardLayout';

export default function Loading() {
  return (
    <DashboardLayout>
      <div className="animate-pulse">
        <div className="mb-8 pb-8 border-b border-dashboard-border">
          <div className="h-4 w-32 bg-dashboard-border rounded mb-4" />
          <div className="h-10 w-80 bg-dashboard-border rounded mb-2" />
          <div className="h-4 w-64 bg-dashboard-border/50 rounded" />
        </div>
        <div className="mb-8">
          <div className="h-7 w-32 bg-dashboard-border rounded mb-4" />
          <div className="space-y-3">
            <div className="h-4 w-full bg-dashboard-border/50 rounded" />
            <div className="h-4 w-5/6 bg-dashboard-border/50 rounded" />
            <div className="h-4 w-4/6 bg-dashboard-border/50 rounded" />
          </div>
        </div>
        <div className="space-y-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="border-l-4 border-dashboard-border pl-4 py-2">
              <div className="h-3 w-24 bg-dashboard-border/50 rounded mb-2" />
              <div className="h-5 w-3/4 bg-dashboard-border rounded mb-2" />
              <div className="h-4 w-full bg-dashboard-border/50 rounded" />
            </div>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
