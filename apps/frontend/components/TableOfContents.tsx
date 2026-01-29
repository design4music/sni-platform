'use client';

import { useEffect, useState } from 'react';

export interface TocSection {
  id: string;
  label: string;
  count?: number;
  children?: TocSection[];
}

interface TableOfContentsProps {
  sections: TocSection[];
}

export default function TableOfContents({ sections }: TableOfContentsProps) {
  const [activeId, setActiveId] = useState<string>('');

  useEffect(() => {
    // Collect all section IDs (including children)
    const allIds: string[] = [];
    sections.forEach(s => {
      allIds.push(s.id);
      s.children?.forEach(c => allIds.push(c.id));
    });

    const observer = new IntersectionObserver(
      (entries) => {
        // Find the first visible section
        const visible = entries
          .filter(e => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);

        if (visible.length > 0) {
          setActiveId(visible[0].target.id);
        }
      },
      {
        rootMargin: '-80px 0px -60% 0px',
        threshold: 0
      }
    );

    // Observe all sections
    allIds.forEach(id => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, [sections]);

  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      const headerOffset = 100;
      const elementPosition = el.getBoundingClientRect().top + window.scrollY;
      window.scrollTo({
        top: elementPosition - headerOffset,
        behavior: 'smooth'
      });
    }
  };

  if (sections.length === 0) return null;

  return (
    <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4">
      <h3 className="text-sm font-semibold mb-3 text-dashboard-text-muted uppercase tracking-wider">
        On This Page
      </h3>
      <nav className="space-y-1">
        {sections.map(section => (
          <div key={section.id}>
            <button
              onClick={() => scrollTo(section.id)}
              className={`block w-full text-left px-3 py-1.5 rounded text-sm transition-colors ${
                activeId === section.id
                  ? 'bg-blue-600/20 text-blue-400 font-medium'
                  : 'text-dashboard-text-muted hover:text-dashboard-text hover:bg-dashboard-border/50'
              }`}
            >
              {section.label}
              {section.count !== undefined && (
                <span className="ml-1 text-xs opacity-60">({section.count})</span>
              )}
            </button>
            {section.children && section.children.length > 0 && (
              <div className="ml-3 mt-1 space-y-0.5 border-l border-dashboard-border pl-2">
                {section.children.map(child => (
                  <button
                    key={child.id}
                    onClick={() => scrollTo(child.id)}
                    className={`block w-full text-left px-2 py-1 rounded text-xs transition-colors ${
                      activeId === child.id
                        ? 'text-blue-400 font-medium'
                        : 'text-dashboard-text-muted hover:text-dashboard-text'
                    }`}
                  >
                    {child.label}
                    {child.count !== undefined && (
                      <span className="ml-1 opacity-60">({child.count})</span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </nav>
    </div>
  );
}
