'use client';

const SOURCES = [
  'Reuters', 'BBC', 'France 24', 'CNN', 'AP News',
  'Financial Times', 'The Guardian', 'Al Jazeera', 'Al Arabiya',
  'Hindustan Times', 'Euronews', 'TASS', 'RT News', 'CGTN',
  'Wall Street Journal', 'ABC News', 'Anadolu Agency',
];

export default function SourceCarousel({ feedCount }: { feedCount: number }) {
  const items = [...SOURCES, ...SOURCES];

  return (
    <section className="pt-8">
      <div className="mb-6">
        <h2 className="text-3xl font-bold">Our Sources</h2>
        <a
          href="/sources"
          className="text-dashboard-text-muted hover:text-blue-300 transition mt-2 inline-block"
        >
          {feedCount}+ international news sources across all regions
        </a>
      </div>

      <a href="/sources" className="block relative overflow-hidden cursor-pointer">
        <div className="pointer-events-none absolute inset-y-0 left-0 w-24 z-10 bg-gradient-to-r from-[#0a0e1a] to-transparent" />
        <div className="pointer-events-none absolute inset-y-0 right-0 w-24 z-10 bg-gradient-to-l from-[#0a0e1a] to-transparent" />

        <div className="flex gap-[3rem] animate-carousel">
          {items.map((name, i) => (
            <span
              key={`${name}-${i}`}
              className="flex-shrink-0 text-[1.5rem] leading-[3.5rem] font-semibold tracking-tight text-white/40 whitespace-nowrap select-none"
            >
              {name}
            </span>
          ))}
        </div>
      </a>
    </section>
  );
}
