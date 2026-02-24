import DashboardLayout from '@/components/DashboardLayout';

export default function Loading() {
  return (
    <DashboardLayout>
      <div className="animate-pulse">
        <div className="mb-4">
          <div className="h-8 w-48 bg-dashboard-border/50 rounded" />
        </div>
        <div className="mb-8 pb-8 border-b border-dashboard-border">
          <div className="h-10 w-3/4 bg-dashboard-border rounded mb-2" />
          <div className="h-4 w-48 bg-dashboard-border/50 rounded" />
        </div>
        <div className="mb-8">
          <div className="h-7 w-32 bg-dashboard-border rounded mb-4" />
          <div className="space-y-3">
            <div className="h-4 w-full bg-dashboard-border/50 rounded" />
            <div className="h-4 w-5/6 bg-dashboard-border/50 rounded" />
            <div className="h-4 w-4/6 bg-dashboard-border/50 rounded" />
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
