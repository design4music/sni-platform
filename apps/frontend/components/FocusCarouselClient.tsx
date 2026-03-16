'use client';

import { useState, useCallback, ReactNode, Children } from 'react';

interface Props {
  children: ReactNode;
  frameSize?: number;
}

export default function FocusCarouselClient({ children, frameSize = 3 }: Props) {
  const items = Children.toArray(children);
  const frames: ReactNode[][] = [];
  for (let i = 0; i < items.length; i += frameSize) {
    frames.push(items.slice(i, i + frameSize));
  }

  const [active, setActive] = useState(0);
  const [visible, setVisible] = useState(0);
  const [fading, setFading] = useState(false);

  const changeTo = useCallback((target: number) => {
    if (target === visible) return;
    setFading(true);
    setTimeout(() => {
      setVisible(target);
      setFading(false);
    }, 300);
  }, [visible]);

  const handleDotClick = (i: number) => {
    setActive(i);
    changeTo(i);
  };

  if (frames.length === 0) return null;

  return (
    <div>
      <div
        className={`grid grid-cols-1 md:grid-cols-3 gap-3 transition-opacity duration-300 ${
          fading ? 'opacity-0' : 'opacity-100'
        }`}
      >
        {frames[visible].map((child, i) => (
          <div key={i}>{child}</div>
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
