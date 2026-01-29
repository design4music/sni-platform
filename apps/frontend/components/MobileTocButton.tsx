'use client';

import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { TocSection } from './TableOfContents';

interface MobileTocButtonProps {
  sections: TocSection[];
}

export default function MobileTocButton({ sections }: MobileTocButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      const headerOffset = 80;
      const elementPosition = el.getBoundingClientRect().top + window.scrollY;
      window.scrollTo({
        top: elementPosition - headerOffset,
        behavior: 'smooth'
      });
    }
    setIsOpen(false);
  };

  if (sections.length === 0) return null;

  return (
    <>
      {/* Floating button - mobile only */}
      <button
        onClick={() => setIsOpen(true)}
        className="lg:hidden fixed bottom-6 right-6 z-50 w-12 h-12 rounded-full bg-blue-600 text-white shadow-lg flex items-center justify-center hover:bg-blue-500 transition-colors"
        aria-label="Table of Contents"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h7" />
        </svg>
      </button>

      {/* Drawer - portal to body */}
      {mounted && isOpen && createPortal(
        <div className="fixed inset-0 z-[100] lg:hidden">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/60"
            onClick={() => setIsOpen(false)}
          />

          {/* Drawer */}
          <div className="absolute bottom-0 left-0 right-0 bg-dashboard-surface border-t border-dashboard-border rounded-t-2xl max-h-[70vh] overflow-y-auto">
            {/* Handle */}
            <div className="flex justify-center py-3">
              <div className="w-10 h-1 rounded-full bg-dashboard-border" />
            </div>

            {/* Header */}
            <div className="px-4 pb-2 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-dashboard-text">On This Page</h3>
              <button
                onClick={() => setIsOpen(false)}
                className="p-2 rounded-lg hover:bg-dashboard-border transition"
              >
                <svg className="w-5 h-5 text-dashboard-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Sections */}
            <nav className="px-4 pb-8 space-y-1">
              {sections.map(section => (
                <div key={section.id}>
                  <button
                    onClick={() => scrollTo(section.id)}
                    className="block w-full text-left px-4 py-3 rounded-lg text-base text-dashboard-text hover:bg-dashboard-border transition"
                  >
                    {section.label}
                    {section.count !== undefined && (
                      <span className="ml-2 text-sm text-dashboard-text-muted">({section.count})</span>
                    )}
                  </button>
                  {section.children && section.children.length > 0 && (
                    <div className="ml-4 space-y-0.5">
                      {section.children.map(child => (
                        <button
                          key={child.id}
                          onClick={() => scrollTo(child.id)}
                          className="block w-full text-left px-4 py-2 rounded-lg text-sm text-dashboard-text-muted hover:text-dashboard-text hover:bg-dashboard-border/50 transition"
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
        </div>,
        document.body
      )}
    </>
  );
}
