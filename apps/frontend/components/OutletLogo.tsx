'use client';

import { useState } from 'react';

interface OutletLogoProps {
  src: string;
  name: string;
  size?: number;
  className?: string;
}

function getInitials(name: string): string {
  return name
    .replace(/[^a-zA-Z0-9\s]/g, '')
    .split(/\s+/)
    .filter(Boolean)
    .map(w => w[0])
    .join('')
    .slice(0, 2)
    .toUpperCase() || '?';
}

export default function OutletLogo({ src, name, size = 20, className = '' }: OutletLogoProps) {
  const [failed, setFailed] = useState(false);

  if (failed || !src) {
    return (
      <span
        className={`inline-flex items-center justify-center rounded bg-dashboard-border text-dashboard-text-muted font-semibold flex-shrink-0 ${className}`}
        style={{ width: size, height: size, fontSize: Math.max(size * 0.4, 8) }}
      >
        {getInitials(name)}
      </span>
    );
  }

  return (
    <img
      src={src}
      alt=""
      width={size}
      height={size}
      className={`object-contain flex-shrink-0 ${className}`}
      onError={() => setFailed(true)}
    />
  );
}
