'use client';

import { useState, useEffect, useCallback } from 'react';
import TrendingCard from './TrendingCard';
import { TrendingEvent } from '@/lib/types';

interface Props {
  events: TrendingEvent[];
  frameSize?: number;
  intervalMs?: number;
}

export default function TrendingCarouselClient({ events, frameSize = 3, intervalMs = 8000 }: Props) {
  const frames: TrendingEvent[][] = [];
  for (let i = 0; i < events.length; i += frameSize) {
    frames.push(events.slice(i, i + frameSize));
  }

  const [active, setActive] = useState(0);
  const [visible, setVisible] = useState(0);
  const [fading, setFading] = useState(false);
  const [paused, setPaused] = useState(false);

  const changeTo = useCallback((target: number) => {
    if (target === visible) return;
    setFading(true);
    setTimeout(() => {
      setVisible(target);
      setFading(false);
    }, 300);
  }, [visible]);

  const next = useCallback(() => {
    setActive(i => {
      const n = (i + 1) % frames.length;
      changeTo(n);
      return n;
    });
  }, [frames.length, changeTo]);

  useEffect(() => {
    if (paused || frames.length <= 1) return;
    const id = setInterval(next, intervalMs);
    return () => clearInterval(id);
  }, [paused, next, intervalMs, frames.length]);

  const handleDotClick = (i: number) => {
    setActive(i);
    changeTo(i);
  };

  if (frames.length === 0) return null;

  return (
    <div
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      <div
        className={`grid grid-cols-1 md:grid-cols-3 gap-4 transition-opacity duration-300 ${
          fading ? 'opacity-0' : 'opacity-100'
        }`}
      >
        {frames[visible].map(event => (
          <TrendingCard key={event.id} event={event} />
        ))}
      </div>

      {frames.length > 1 && (
        <div className="flex justify-center gap-2 mt-4">
          {frames.map((_, i) => (
            <button
              key={i}
              onClick={() => handleDotClick(i)}
              className={`w-2 h-2 rounded-full transition-all ${
                i === active
                  ? 'bg-blue-400 w-4'
                  : 'bg-dashboard-border hover:bg-dashboard-text-muted'
              }`}
              aria-label={`Show frame ${i + 1}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
