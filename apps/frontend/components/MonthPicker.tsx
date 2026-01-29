'use client';

import Link from 'next/link';
import { useRef, useEffect } from 'react';

interface MonthPickerProps {
  months: string[];  // YYYY-MM format, already sorted descending
  currentMonth: string;
  baseUrl: string;
}

function formatMonth(month: string): string {
  const [year, m] = month.split('-');
  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const monthIndex = parseInt(m, 10) - 1;
  return `${monthNames[monthIndex]} ${year}`;
}

export default function MonthPicker({ months, currentMonth, baseUrl }: MonthPickerProps) {
  const activeRef = useRef<HTMLAnchorElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Scroll active month into view on mount
  useEffect(() => {
    if (activeRef.current && containerRef.current) {
      const container = containerRef.current;
      const active = activeRef.current;
      const containerRect = container.getBoundingClientRect();
      const activeRect = active.getBoundingClientRect();

      // Center the active element in the container
      const scrollLeft = active.offsetLeft - container.offsetWidth / 2 + active.offsetWidth / 2;
      container.scrollLeft = Math.max(0, scrollLeft);
    }
  }, [currentMonth]);

  if (months.length === 0) {
    return null;
  }

  return (
    <div>
      <h3 className="text-lg font-semibold mb-3">View by Month</h3>
      <div
        ref={containerRef}
        className="flex gap-2 overflow-x-auto pb-2 scrollbar-thin"
        style={{ scrollbarWidth: 'thin' }}
      >
        {months.map((month) => {
          const isActive = month === currentMonth;
          const href = `${baseUrl}?month=${month}`;

          return (
            <Link
              key={month}
              href={href}
              ref={isActive ? activeRef : null}
              className={`
                flex-shrink-0 px-3 py-1.5 rounded-md text-sm font-medium
                transition-colors whitespace-nowrap
                ${isActive
                  ? 'bg-blue-500 text-white'
                  : 'bg-dashboard-surface border border-dashboard-border text-dashboard-text-muted hover:text-dashboard-text hover:border-blue-500/50'
                }
              `}
            >
              {formatMonth(month)}
            </Link>
          );
        })}
      </div>
    </div>
  );
}
