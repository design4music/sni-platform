/**
 * Shared flag image component.
 *
 * Single source of truth for country flags in the UI. Matches the inline-flag
 * style used on event-page accordions (16x12 from flagcdn, no border wrapper,
 * no filter). Use this anywhere a country flag appears in a pill, header, or
 * inline next to a label.
 *
 * For decorative or subdued contexts (legacy CountryAccordion), prefer this
 * component over a one-off implementation; flag style should be consistent
 * across the app.
 */

interface FlagImgProps {
  iso2: string | null | undefined;
  /** Render width in px. Aspect ratio is fixed at 4:3 (16x12 ratio). */
  size?: number;
  className?: string;
}

export default function FlagImg({ iso2, size = 16, className = '' }: FlagImgProps) {
  if (!iso2 || iso2.length !== 2) return null;
  const code = iso2.toLowerCase();
  const h = Math.round((size * 12) / 16);
  // Pick the closest flagcdn size variant. The CDN serves common widths so
  // small sizes get a crisp 16x12 endpoint and larger sizes step up.
  const url = size <= 18 ? `https://flagcdn.com/16x12/${code}.png` : `https://flagcdn.com/w40/${code}.png`;
  return (
    <img
      src={url}
      alt={iso2.toUpperCase()}
      width={size}
      height={h}
      className={`inline-block flex-shrink-0 ${className}`}
      loading="lazy"
    />
  );
}
