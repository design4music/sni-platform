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

  // Wrap the logo in a light slate "chip" so transparent PNGs with dark
  // foreground content stay legible against the dark dashboard. Tiny inset
  // (~6%) gives logos breathing room without shrinking them noticeably.
  const inset = Math.max(2, Math.round(size * 0.06));
  return (
    <span
      className={`inline-flex items-center justify-center rounded bg-slate-200 overflow-hidden flex-shrink-0 ${className}`}
      style={{ width: size, height: size, padding: inset }}
    >
      <img
        src={src}
        alt=""
        className="object-contain w-full h-full"
        onError={() => setFailed(true)}
      />
    </span>
  );
}
