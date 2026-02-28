'use client';

import { useState } from 'react';
import Link from 'next/link';
import { SignalCategoryEntry, SignalType, SIGNAL_LABELS } from '@/lib/types';
import TemporalHeatmap from './TemporalHeatmap';

interface CategoryMeta {
  type: SignalType;
  icon: string;
  badge: string;
}

interface Props {
  signals: SignalCategoryEntry[];
  categories: CategoryMeta[];
}

export default function SignalAccordion({ signals, categories }: Props) {
  const [open, setOpen] = useState<Set<SignalType>>(new Set());

  const toggle = (type: SignalType) => {
    setOpen(prev => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  };

  const grouped = new Map<SignalType, SignalCategoryEntry[]>();
  for (const s of signals) {
    const list = grouped.get(s.signal_type) || [];
    list.push(s);
    grouped.set(s.signal_type, list);
  }

  return (
    <div className="space-y-2">
      {categories.map(({ type, icon, badge }) => {
        const items = grouped.get(type) || [];
        if (items.length === 0) return null;
        const isOpen = open.has(type);

        return (
          <div key={type} className="rounded-lg border border-dashboard-border bg-dashboard-surface overflow-hidden">
            <button
              onClick={() => toggle(type)}
              className="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/[0.02] transition text-left"
            >
              <span className={`inline-flex items-center justify-center w-6 h-6 rounded text-xs font-bold border ${badge}`}>
                {icon}
              </span>
              <span className="text-sm font-medium text-dashboard-text flex-1">
                {SIGNAL_LABELS[type]}
              </span>
              <span className="text-xs text-dashboard-text-muted">{items.length}</span>
              <svg
                className={`w-4 h-4 text-dashboard-text-muted transition-transform ${isOpen ? 'rotate-180' : ''}`}
                fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {isOpen && (
              <div className="px-4 pb-4">
                <TemporalHeatmap signals={items} />
                <div className="mt-3 text-right">
                  <Link
                    href={`/signals/${type}`}
                    className="text-xs text-blue-400 hover:text-blue-300 transition"
                  >
                    View all {SIGNAL_LABELS[type].toLowerCase()} &rarr;
                  </Link>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
