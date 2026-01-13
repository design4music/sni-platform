import { ReactNode } from 'react';
import Logo from './Logo';
import Navigation from './Navigation';

interface ReadingLayoutProps {
  children: ReactNode;
  sidebar?: ReactNode;
}

export default function ReadingLayout({ children, sidebar }: ReadingLayoutProps) {
  return (
    <div className="min-h-screen bg-reading-bg text-reading-text">
      <header className="border-b border-dashboard-border bg-dashboard-surface sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <Logo />
            <Navigation />
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className={sidebar ? "grid grid-cols-1 lg:grid-cols-3 gap-8" : ""}>
          <div className={sidebar ? "lg:col-span-2" : ""}>
            <article className="prose prose-lg max-w-none">
              {children}
            </article>
          </div>
          {sidebar && (
            <aside className="space-y-6">
              <div className="bg-dashboard-bg text-dashboard-text p-6 rounded-lg">
                {sidebar}
              </div>
            </aside>
          )}
        </div>
      </main>
    </div>
  );
}
