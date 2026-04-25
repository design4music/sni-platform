/**
 * Small outlet favicon — extracted from ExpandableTitles so it can be
 * reused as a server or client component. Pure presentation, no hooks.
 *
 * Tries the local /logos/{domain}.png path first (matches the asset
 * pattern used elsewhere). When the publisher name isn't in the static
 * domain map, falls back to a single-letter circle for visual consistency.
 *
 * If a domain is known directly (e.g. from feeds.source_domain), pass it
 * as `domain` to skip the lookup table. Otherwise just pass `publisher`.
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
  const resolved = domain ? cleanDomain(domain) : KNOWN_DOMAINS[publisher];
  if (!resolved) {
    return (
      <span
        className={`rounded bg-dashboard-border flex items-center justify-center text-[10px] text-dashboard-text-muted flex-shrink-0 ${className}`}
        style={{ width: size, height: size }}
      >
        {publisher.charAt(0).toUpperCase()}
      </span>
    );
  }
  // Light "chip" wrapper so logos with transparent backgrounds and dark
  // foreground content (e.g. Die Zeit's black "Z", FAZ's wordmark) are
  // legible against the dark dashboard. Mid-light slate works for both
  // black-on-transparent and white-on-coloured logos.
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
      />
    </span>
  );
}
