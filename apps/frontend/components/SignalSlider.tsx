'use client';

import { useState } from 'react';
import { TopSignal } from '@/lib/types';

interface SignalSliderProps {
  title: string;
  signals: TopSignal[];
}

export default function SignalSlider({ title, signals }: SignalSliderProps) {
  const [index, setIndex] = useState(0);

  if (!signals || signals.length === 0) return null;

  const current = signals[index];
  const total = signals.length;

  const prev = () => setIndex((i) => (i === 0 ? total - 1 : i - 1));
  const next = () => setIndex((i) => (i === total - 1 ? 0 : i + 1));

  return (
    <div className="p-4 border border-dashboard-border bg-dashboard-surface rounded-lg flex flex-col h-full">
      {/* Header */}
      <div className="text-xs text-dashboard-text-muted uppercase tracking-wide mb-2">
        {title}
      </div>

      {/* Content */}
      <div className="flex-1 min-h-[80px]">
        <div className="flex items-center justify-between mb-1">
          <h4 className="font-semibold text-base">
            {current.value}
          </h4>
          <span className="text-xs text-dashboard-text-muted/60 tabular-nums">
            {current.count}
          </span>
        </div>
        {current.context && (
          <p className="text-xs text-dashboard-text-muted leading-relaxed line-clamp-3">
            {current.context}
          </p>
        )}
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between mt-3 pt-2 border-t border-dashboard-border/50">
        <button
          onClick={prev}
          className="text-dashboard-text-muted hover:text-dashboard-text p-1"
          aria-label="Previous"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        {/* Dots */}
        <div className="flex items-center gap-1.5">
          {signals.map((_, i) => (
            <button
              key={i}
              onClick={() => setIndex(i)}
              className={`w-1.5 h-1.5 rounded-full transition-colors ${
                i === index
                  ? 'bg-blue-500'
                  : 'bg-dashboard-border hover:bg-dashboard-text-muted'
              }`}
              aria-label={`Go to item ${i + 1}`}
            />
          ))}
        </div>

        <button
          onClick={next}
          className="text-dashboard-text-muted hover:text-dashboard-text p-1"
          aria-label="Next"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  );
}
