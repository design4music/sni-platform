'use client';

import Link from 'next/link';
import { useTranslations } from 'next-intl';

export default function Logo() {
  const t = useTranslations('common');
  return (
    <Link href="/" className="flex items-center gap-3">
      <div className="text-2xl font-bold tracking-tight">
        <span className="text-blue-500">WORLD</span>
        <span className="text-white">BRIEF</span>
      </div>
      <div className="hidden md:block text-sm text-gray-400" style={{ marginLeft: '0.75rem' }}>
        {t('slogan')}
      </div>
    </Link>
  );
}
