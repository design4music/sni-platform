'use client';

import { useState } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';

interface Props {
  entityType: 'event' | 'ctm';
  entityId: string;
}

export default function ExtractButton({ entityType, entityId }: Props) {
  const { data: session } = useSession();
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [coherenceWarning, setCoherenceWarning] = useState<{
    reason: string;
    topics: string[];
  } | null>(null);

  if (!session?.user) {
    return (
      <a
        href="/auth/signin"
        className="inline-block text-sm px-4 py-2 rounded bg-dashboard-border text-dashboard-text-muted hover:text-dashboard-text transition-colors"
      >
        Sign in to extract &amp; analyse
      </a>
    );
  }

  async function handleClick() {
    setLoading(true);
    setError(null);
    setCoherenceWarning(null);

    try {
      const resp = await fetch('/api/extract-narratives', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ entity_type: entityType, entity_id: entityId }),
      });

      if (!resp.ok) {
        const data = await resp.json().catch(() => ({ error: 'Request failed' }));
        throw new Error(data.error || `Error ${resp.status}`);
      }

      const data = await resp.json();

      // Coherence check failed
      if (data.coherent === false) {
        setCoherenceWarning({
          reason: data.reason,
          topics: data.topics || [],
        });
        setLoading(false);
        return;
      }

      if (data.first_narrative_id) {
        router.push(`/analysis/${data.first_narrative_id}`);
      } else {
        setError('No narratives were extracted');
        setLoading(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setLoading(false);
    }
  }

  if (coherenceWarning) {
    return (
      <div className="space-y-2">
        <div className="text-xs text-amber-300 bg-amber-900/20 border border-amber-700/50 rounded-lg p-3 leading-relaxed">
          <p className="font-medium mb-1">Mixed topic cluster detected</p>
          <p>{coherenceWarning.reason}</p>
          {coherenceWarning.topics.length > 0 && (
            <ul className="mt-1.5 space-y-0.5 list-disc list-inside text-amber-200/80">
              {coherenceWarning.topics.map((t, i) => (
                <li key={i}>{t}</li>
              ))}
            </ul>
          )}
        </div>
      </div>
    );
  }

  return (
    <div>
      <button
        onClick={handleClick}
        disabled={loading}
        className="inline-flex items-center gap-2 text-sm px-4 py-2 rounded bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-wait text-white transition-colors"
      >
        {loading ? (
          <>
            <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            Extracting narrative frames...
          </>
        ) : (
          'Extract & Analyse'
        )}
      </button>
      {error && (
        <p className="mt-2 text-sm text-red-400">{error}</p>
      )}
    </div>
  );
}
