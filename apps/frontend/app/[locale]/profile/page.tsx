import type { Metadata } from 'next';
import { getTranslations, getLocale } from 'next-intl/server';
import { auth } from '@/auth';
import { redirect } from 'next/navigation';
import { getCentroidsByClass } from '@/lib/queries';
import { getCentroidLabel } from '@/lib/types';
import DashboardLayout from '@/components/DashboardLayout';
import ProfileClient from '@/components/ProfileClient';

export const dynamic = 'force-dynamic';

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('profile');
  return { title: t('title') };
}

export default async function ProfilePage() {
  const session = await auth();
  if (!session?.user) {
    redirect('/auth/signin');
  }

  const locale = await getLocale();
  const t = await getTranslations('profile');
  const tCentroids = await getTranslations('centroids');

  // Fetch GEO centroids only for the focus country picker
  const geoCentroids = await getCentroidsByClass('geo', locale);
  const centroidOptions = geoCentroids
    .filter(c => !c.id.startsWith('NON-STATE-'))
    .map(c => ({ id: c.id, label: getCentroidLabel(c.id, c.label, tCentroids) }))
    .sort((a, b) => a.label.localeCompare(b.label));

  return (
    <DashboardLayout title={t('title')}>
      <ProfileClient centroidOptions={centroidOptions} />
    </DashboardLayout>
  );
}
