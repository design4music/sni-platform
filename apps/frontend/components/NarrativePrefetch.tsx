'use client';

import { useEffect, useRef, useState } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import ExtractButton from './ExtractButton';

export default function NarrativePrefetch({ entityType, entityId }: {
  entityType: 'event' | 'ctm';
  entityId: string;
}) {
  const { data: session, status } = useSession();
  const router = useRouter();
  const t = useTranslations('stanceCluster');
  const tEvent = useTranslations('event');
  const fired = useRef(false);
  const [state, setState] = useState<'loading' | 'done' | 'failed'>('loading');

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
        if (data.has_stance && data.status !== 'cached') {
          router.refresh();
          setState('done');
        } else if (data.has_stance) {
          setState('done');
        } else {
          setState('failed');
        }
      })
      .catch((err) => {
        console.error('[NarrativePrefetch] error:', err);
        setState('failed');
      });
  }, [session, status, entityType, entityId, router]);

  if (status === 'unauthenticated' || state === 'done') return null;

  // Auto-extraction failed -- fall back to manual extract button
  if (state === 'failed') {
    return (
      <div className="bg-dashboard-border/30 rounded-lg p-5 space-y-3">
        <h3 className="text-sm font-semibold text-dashboard-text">{tEvent('narrativeAnalysis')}</h3>
        <p className="text-xs text-dashboard-text-muted leading-relaxed">
          {tEvent('extractDescription')}
        </p>
        <ExtractButton entityType="event" entityId={entityId} />
      </div>
    );
  }

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
