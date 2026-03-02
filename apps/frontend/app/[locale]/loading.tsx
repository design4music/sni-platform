import DashboardLayout from '@/components/DashboardLayout';

export default function Loading() {
  return (
    <DashboardLayout>
      <div className="text-center py-24">
        <div className="inline-block animate-pulse">
          <p className="text-xl text-dashboard-text-muted">Loading...</p>
        </div>
      </div>
    </DashboardLayout>
  );
}
