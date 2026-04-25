'use client';

import { useState } from 'react';

/**
 * Small outlet favicon. Used in event-page accordions, the sibling-outlets
 * sidebar block, and anywhere a publisher logo appears inline.
 *
 * Tries the local /logos/{domain}.png path. Two fallback paths to a typed
 * single-letter chip (same shape, same size — visually consistent with
 * real logos at the layout level):
 *   1. No domain known for this publisher (lookup miss).
 *   2. Logo file 404s at runtime (onError handler).
 *
 * Real logos sit on a light slate "chip" so transparent PNGs with dark
 * foregrounds (Die Zeit, FAZ wordmarks) stay legible against the dark
 * dashboard. The initials fallback uses the dashboard-border colour so
 * a visual signal distinguishes typed letters from real artwork.
 *
 * If a domain is known directly (feeds.source_domain), pass it as
 * `domain` to skip the lookup table.
 */

interface Props {
  publisher: string;
  /** Optional explicit domain (overrides the lookup map) */
  domain?: string | null;
  size?: number;
  className?: string;
}

const KNOWN_DOMAINS: Record<string, string> = {
  Reuters: 'reuters.com',
  'AP News': 'apnews.com',
  BBC: 'bbc.com',
  'BBC World': 'bbc.com',
  'Financial Times': 'ft.com',
  'The Wall Street Journal': 'wsj.com',
  'Wall Street Journal': 'wsj.com',
  'The New York Times': 'nytimes.com',
  'New York Times': 'nytimes.com',
  'The Washington Post': 'washingtonpost.com',
  'Washington Post': 'washingtonpost.com',
  NPR: 'npr.org',
  'The Guardian': 'theguardian.com',
  CNN: 'cnn.com',
  'Al Jazeera': 'aljazeera.com',
  Bloomberg: 'bloomberg.com',
  POLITICO: 'politico.com',
  Forbes: 'forbes.com',
  'ABC News': 'abcnews.go.com',
  'NBC News': 'nbcnews.com',
  'CBS News': 'cbsnews.com',
  DW: 'dw.com',
  'Deutsche Welle': 'dw.com',
  'France 24': 'france24.com',
  'The Times of Israel': 'timesofisrael.com',
  'Times of Israel': 'timesofisrael.com',
  'South China Morning Post': 'scmp.com',
  'Der Spiegel': 'spiegel.de',
  Handelsblatt: 'handelsblatt.com',
  'Frankfurter Allgemeine': 'faz.net',
  'Süddeutsche Zeitung': 'sueddeutsche.de',
  'Die Zeit': 'zeit.de',
  Tagesschau: 'tagesschau.de',
  Haaretz: 'haaretz.com',
  'Jerusalem Post': 'jpost.com',
  'Lenta.ru': 'lenta.ru',
  'TASS (EN)': 'tass.com',
  TASS: 'tass.ru',
  CGTN: 'cgtn.com',
  'Al-Ahram': 'ahram.org.eg',
  'Al Arabiya': 'alarabiya.net',
  'Anadolu Agency': 'aa.com.tr',
  Euronews: 'euronews.com',
  'Fox News': 'foxnews.com',
  'Hindustan Times': 'hindustantimes.com',
  'Times of India': 'timesofindia.indiatimes.com',
  'Le Figaro': 'lefigaro.fr',
  'Straits Times': 'straitstimes.com',
  'The Telegraph': 'telegraph.co.uk',
  NDTV: 'ndtv.com',
  Gazeta: 'gazeta.ru',
  'Gazeta.ru': 'gazeta.ru',
};

function cleanDomain(d: string): string {
  return d
    .replace(/^https?:\/\//, '')
    .replace(/^www\./, '')
    .replace(/\/$/, '');
}

export default function PublisherFavicon({ publisher, domain, size = 20, className = '' }: Props) {
  const [failed, setFailed] = useState(false);
  const resolved = domain ? cleanDomain(domain) : KNOWN_DOMAINS[publisher];

  if (!resolved || failed) {
    // Letter chip — same dimensions as the real-logo chip so list rows stay
    // aligned regardless of whether the logo loaded.
    return (
      <span
        className={`inline-flex items-center justify-center rounded bg-dashboard-border text-dashboard-text-muted font-semibold flex-shrink-0 ${className}`}
        style={{ width: size, height: size, fontSize: Math.max(size * 0.45, 9) }}
      >
        {publisher.charAt(0).toUpperCase()}
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center justify-center rounded bg-slate-200 overflow-hidden flex-shrink-0 ${className}`}
      style={{ width: size, height: size }}
    >
      <img
        src={`/logos/${resolved}.png`}
        alt=""
        className="object-contain w-full h-full"
        loading="lazy"
        onError={() => setFailed(true)}
      />
    </span>
  );
}
