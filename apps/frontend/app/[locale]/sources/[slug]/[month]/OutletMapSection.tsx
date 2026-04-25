'use client';

import dynamic from 'next/dynamic';

const WorldMap = dynamic(() => import('@/components/WorldMap'), { ssr: false });

interface OutletMapSectionProps {
  centroids: Array<{
    id: string;
    label: string;
    iso_codes: string[];
    source_count: number;
    /** Optional stance overlay. When present (even null) WorldMap
     *  switches to stance-coloring + stance legend automatically. */
    stance?: number | null;
    tone?: string | null;
    confidence?: 'low' | 'medium' | 'high' | null;
  }>;
}

export default function OutletMapSection({ centroids }: OutletMapSectionProps) {
  return <WorldMap centroids={centroids} />;
}
