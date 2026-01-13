import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';

export default function NotFound() {
  return (
    <DashboardLayout>
      <div className="text-center py-24">
        <h1 className="text-6xl font-bold mb-4">404</h1>
        <p className="text-xl text-dashboard-text-muted mb-8">
          The page you are looking for does not exist
        </p>
        <Link
          href="/"
          className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          Return Home
        </Link>
      </div>
    </DashboardLayout>
  );
}
