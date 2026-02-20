'use client';

import dynamic from 'next/dynamic';

const CentroidMiniMap = dynamic(() => import('./CentroidMiniMap'), { ssr: false });

interface Props {
  isoCodes: string[];
}

export default function CentroidMiniMapWrapper({ isoCodes }: Props) {
  return <CentroidMiniMap isoCodes={isoCodes} />;
}
