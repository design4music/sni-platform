'use client';

import { useEffect, useRef, useState } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';

export default function NarrativePrefetch({ entityType, entityId }: {
  entityType: 'event' | 'ctm';
  entityId: string;
}) {
  const { data: session, status } = useSession();
  const router = useRouter();
  const t = useTranslations('stanceCluster');
  const fired = useRef(false);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (status === 'loading' || !session?.user || fired.current) return;
    fired.current = true;

    fetch('/api/extract-narratives', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entity_type: entityType, entity_id: entityId }),
    })
      .then((r) => r.json())
      .then((data) => {
        console.log('[NarrativePrefetch] response:', data);
        if (data.has_stance) router.refresh();
      })
      .catch((err) => { console.error('[NarrativePrefetch] error:', err); })
      .finally(() => setDone(true));
  }, [session, status, entityType, entityId, router]);

  // Hide after done, or if user is not signed in
  if (done || status === 'unauthenticated') return null;

  return (
    <div className="bg-dashboard-border/30 rounded-lg p-5 space-y-2">
      <h3 className="text-sm font-semibold text-dashboard-text">{t('title')}</h3>
      <div className="flex items-center gap-2 text-xs text-dashboard-text-muted">
        <span className="inline-block w-3.5 h-3.5 border-2 border-blue-400/30 border-t-blue-400 rounded-full animate-spin" />
        {t('analysing')}
      </div>
    </div>
  );
}
