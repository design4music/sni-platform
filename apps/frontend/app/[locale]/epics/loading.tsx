import DashboardLayout from '@/components/DashboardLayout';

export default function Loading() {
  return (
    <DashboardLayout>
      <div className="animate-pulse">
        <div className="h-9 w-64 bg-dashboard-border rounded mb-6" />
        <div className="h-10 w-full bg-dashboard-border/30 rounded-lg mb-6" />
        <div className="grid gap-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-28 w-full bg-dashboard-border/30 rounded-lg" />
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
