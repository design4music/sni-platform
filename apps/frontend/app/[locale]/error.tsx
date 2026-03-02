'use client';

import { useEffect } from 'react';
import DashboardLayout from '@/components/DashboardLayout';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <DashboardLayout>
      <div className="text-center py-24">
        <h1 className="text-4xl font-bold mb-4">Something went wrong</h1>
        <p className="text-xl text-dashboard-text-muted mb-8">
          {error.message || 'An unexpected error occurred'}
        </p>
        <button
          onClick={reset}
          className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          Try again
        </button>
      </div>
    </DashboardLayout>
  );
}
