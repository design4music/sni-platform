/**
 * Shared person icon. Use anywhere a public-figure entity is rendered
 * alongside a country flag (heatmap, volume chart, stance pills).
 * Single source of truth so the visual stays consistent across the app.
 */

interface Props {
  className?: string;
}

export default function PersonIcon({ className = 'w-3.5 h-3.5' }: Props) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <circle cx="12" cy="7" r="3.5" />
      <path d="M4 21c0-4.418 3.582-7 8-7s8 2.582 8 7" />
    </svg>
  );
}
