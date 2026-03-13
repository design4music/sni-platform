'use client';

import { useEffect, useRef } from 'react';
import { useSession } from 'next-auth/react';

/**
 * Invisible component that pre-triggers comparative analysis in the background.
 * Placed on the event page so the analysis is cached by the time the user
 * clicks "Deep Analysis" in the sidebar.
 */
export default function AnalysisPrefetch({ entityType, entityId }: {
  entityType: string;
  entityId: string;
}) {
  const { data: session } = useSession();
  const fired = useRef(false);

  useEffect(() => {
    if (!session?.user) return;
    if (fired.current) return;
    fired.current = true;

    fetch('/api/rai-analyse-comparative', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entity_type: entityType, entity_id: entityId }),
    }).catch(() => {});  // silent -- prefetch is best-effort
  }, [session, entityType, entityId]);

  return null;
}
