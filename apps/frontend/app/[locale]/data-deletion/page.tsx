import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';

export const metadata: Metadata = {
  title: 'Data Deletion - WorldBrief',
};

export default function DataDeletionPage() {
  return (
    <DashboardLayout>
      <div className="max-w-2xl mx-auto py-12">
        <h1 className="text-3xl font-bold mb-6">Data Deletion Instructions</h1>
        <div className="space-y-4 text-dashboard-text-muted">
          <p>
            If you signed in with Facebook and want to delete your data from WorldBrief,
            you can do so in two ways:
          </p>
          <ol className="list-decimal list-inside space-y-2">
            <li>
              <strong className="text-white">From your profile:</strong> Sign in, go to your
              Profile page, and request account deletion.
            </li>
            <li>
              <strong className="text-white">By email:</strong> Send a request to{' '}
              <a href="mailto:support@worldbrief.info" className="text-blue-400 hover:text-blue-300">
                support@worldbrief.info
              </a>{' '}
              from the email address associated with your account. We will delete your data
              within 30 days and confirm by email.
            </li>
          </ol>
          <p>
            Deleted data includes your account information, saved preferences, and any
            analysis history. This action is irreversible.
          </p>
        </div>
      </div>
    </DashboardLayout>
  );
}
