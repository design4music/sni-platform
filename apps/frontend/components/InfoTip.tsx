/**
 * Shared "i" hover/tap tooltip.
 *
 * Pure CSS — `group-hover` for desktop pointer, `group-focus-within`
 * for tap-and-release on mobile (`tabIndex={0}` makes the trigger
 * focusable). Tooltip stays open until the user taps elsewhere.
 *
 * Positioning:
 *   - On phones (<sm): the tooltip is `position: fixed` and centered
 *     on the viewport — guarantees it stays fully visible regardless
 *     of where the trigger sits horizontally. Width is clamped to
 *     `calc(100vw - 1.5rem)` so it never causes page horizontal
 *     overflow.
 *   - On sm+: the tooltip is absolutely positioned above the trigger
 *     (classic floating-tooltip behaviour).
 *
 * Pass `text` for a single-string tooltip, or `children` for rich
 * multi-line content. `children` wins when both are present.
 */

import { ReactNode } from 'react';

interface Props {
  text?: string;
  children?: ReactNode;
  /** Override desktop tooltip width. Default ~14rem; `wide` is ~18rem
   *  for richer multi-line content. (Phones always use a clamped width
   *  derived from the viewport.) */
  width?: 'normal' | 'wide';
  className?: string;
}

export default function InfoTip({ text, children, width = 'normal', className = '' }: Props) {
  const desktopWidthClass = width === 'wide' ? 'sm:w-72' : 'sm:w-56';
  return (
    <span
      tabIndex={0}
      className={`group relative inline-block ml-1 cursor-help align-middle outline-none ${className}`}
    >
      <span className="text-blue-400/70 text-[9px] font-semibold border border-blue-400/30 rounded-full w-3.5 h-3.5 inline-flex items-center justify-center leading-none">
        i
      </span>
      <span
        className={`
          invisible opacity-0
          group-hover:visible group-hover:opacity-100
          group-focus-within:visible group-focus-within:opacity-100
          fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
          w-[calc(100vw-1.5rem)] max-w-sm
          sm:absolute sm:top-auto sm:bottom-full sm:translate-y-0 sm:mb-1
          ${desktopWidthClass}
          px-3 py-2 bg-dashboard-surface border border-dashboard-border rounded
          text-[11px] text-dashboard-text-muted z-50 shadow-lg
          text-left leading-snug pointer-events-none transition-opacity
        `}
      >
        {children ?? text}
      </span>
    </span>
  );
}
