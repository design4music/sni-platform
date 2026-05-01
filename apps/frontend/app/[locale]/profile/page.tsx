import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';
import { auth } from '@/auth';
import { redirect } from 'next/navigation';
import DashboardLayout from '@/components/DashboardLayout';
import ProfileClient from '@/components/ProfileClient';

export const dynamic = 'force-dynamic';

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('profile');
  return {
    title: t('title'),
    robots: { index: false, follow: false },
  };
}

export default async function ProfilePage() {
  const session = await auth();
  if (!session?.user) {
    redirect('/auth/signin');
  }

  const t = await getTranslations('profile');

  return (
    <DashboardLayout title={t('title')}>
      <ProfileClient />
    </DashboardLayout>
  );
}
