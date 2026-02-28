import DashboardLayout from '@/components/DashboardLayout';

export default function Loading() {
  return (
    <DashboardLayout>
      <div className="animate-pulse">
        {/* Header */}
        <div className="mb-8">
          <div className="h-10 w-72 bg-dashboard-border rounded mb-2" />
          <div className="h-5 w-96 bg-dashboard-border/50 rounded" />
        </div>

        {/* Graph placeholder */}
        <div className="h-80 bg-dashboard-surface border border-dashboard-border rounded-lg mb-8" />

        {/* Category cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 7 }).map((_, i) => (
            <div key={i} className="h-24 bg-dashboard-surface border border-dashboard-border rounded-lg" />
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
