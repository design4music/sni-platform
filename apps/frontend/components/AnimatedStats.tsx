'use client';

import { useEffect, useRef, useState } from 'react';

interface Stat {
  value: number;
  suffix: string;
  label: string;
  icon: React.ReactNode;
}

function useCountUp(target: number, duration: number, trigger: boolean) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (!trigger) return;
    let start = 0;
    const startTime = performance.now();

    function step(now: number) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(eased * target);
      if (current !== start) {
        start = current;
        setCount(current);
      }
      if (progress < 1) {
        requestAnimationFrame(step);
      }
    }

    requestAnimationFrame(step);
  }, [target, duration, trigger]);

  return count;
}

function StatCard({ stat, visible, delay }: { stat: Stat; visible: boolean; delay: number }) {
  const count = useCountUp(stat.value, 1800, visible);

  return (
    <div
      className="flex flex-col items-center text-center transition-all duration-700 ease-out"
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? 'translateY(0)' : 'translateY(30px)',
        transitionDelay: `${delay}ms`,
      }}
    >
      <div className="w-16 h-16 md:w-20 md:h-20 rounded-2xl bg-blue-500/10 border border-blue-500/20
                      flex items-center justify-center mb-4 text-blue-400">
        {stat.icon}
      </div>
      <p className="text-4xl md:text-5xl lg:text-6xl font-bold text-dashboard-text tabular-nums">
        {count.toLocaleString()}{stat.suffix}
      </p>
      <p className="text-sm md:text-base text-dashboard-text-muted mt-2">{stat.label}</p>
    </div>
  );
}

// SVG icons as components
const RssIcon = (
  <svg className="w-8 h-8 md:w-10 md:h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12.75 19.5v-.75a7.5 7.5 0 00-7.5-7.5H4.5m0-6.75h.75c7.87 0 14.25 6.38 14.25 14.25v.75M6 18.75a.75.75 0 11-1.5 0 .75.75 0 011.5 0z" />
  </svg>
);

const LanguageIcon = (
  <svg className="w-8 h-8 md:w-10 md:h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 21l5.25-11.25L21 21m-9-3h7.5M3 5.621a48.474 48.474 0 016-.371m0 0c1.12 0 2.233.038 3.334.114M9 5.25V3m3.334 2.364C11.176 10.658 7.69 15.08 3 17.502m9.334-12.138c.896.061 1.785.147 2.666.257m-4.589 8.495a18.023 18.023 0 01-3.827-5.802" />
  </svg>
);

const ArticleIcon = (
  <svg className="w-8 h-8 md:w-10 md:h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 7.5h1.5m-1.5 3h1.5m-7.5 3h7.5m-7.5 3h7.5m3-9h3.375c.621 0 1.125.504 1.125 1.125V18a2.25 2.25 0 01-2.25 2.25M16.5 7.5V18a2.25 2.25 0 002.25 2.25M16.5 7.5V4.875c0-.621-.504-1.125-1.125-1.125H4.125C3.504 3.75 3 4.254 3 4.875V18a2.25 2.25 0 002.25 2.25h13.5M6 7.5h3v3H6v-3z" />
  </svg>
);

const GlobeIcon = (
  <svg className="w-8 h-8 md:w-10 md:h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 003 12c0-1.605.42-3.113 1.157-4.418" />
  </svg>
);

interface AnimatedStatsProps {
  feedCount: number;
  languageCount: number;
  dailyArticles: number;
  centroidCount: number;
}

export default function AnimatedStats({
  feedCount,
  languageCount,
  dailyArticles,
  centroidCount,
}: AnimatedStatsProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.3 }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const stats: Stat[] = [
    { value: feedCount, suffix: '+', label: 'RSS feeds monitored', icon: RssIcon },
    { value: languageCount, suffix: '+', label: 'languages covered', icon: LanguageIcon },
    { value: dailyArticles, suffix: '+', label: 'articles per day', icon: ArticleIcon },
    { value: centroidCount, suffix: '', label: 'countries & themes tracked', icon: GlobeIcon },
  ];

  return (
    <section ref={ref} id="how-it-works" className="border-t border-dashboard-border pt-12">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 md:gap-12 mb-10">
        {stats.map((stat, i) => (
          <StatCard key={stat.label} stat={stat} visible={visible} delay={i * 150} />
        ))}
      </div>

      <p className="text-center text-dashboard-text-muted max-w-2xl mx-auto mb-6">
        WorldBrief aggregates global reporting, filters for strategic relevance,
        and synthesizes it into structured briefings by geography and theme.
      </p>

      <p className="text-center text-sm text-dashboard-text-muted/70">
        All summaries are AI-generated.{' '}
        <a href="/disclaimer" className="text-blue-400/70 hover:text-blue-300 underline">
          Learn more about our method
        </a>
      </p>
    </section>
  );
}
