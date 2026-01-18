import { ReactNode } from 'react';
import Logo from './Logo';
import Navigation from './Navigation';
import Footer from './Footer';

interface DashboardLayoutProps {
  children: ReactNode;
  title?: string;
  sidebar?: ReactNode;
  fullWidthContent?: ReactNode;
}

export default function DashboardLayout({ children, title, sidebar, fullWidthContent }: DashboardLayoutProps) {
  return (
    <div className="min-h-screen bg-dashboard-surface text-dashboard-text bg-texture-grid">
      <header className="border-b border-dashboard-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <Logo />
            <Navigation />
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {title && (
          <h1 className="text-4xl font-bold mb-8">{title}</h1>
        )}

        <div className={sidebar ? "grid grid-cols-1 lg:grid-cols-3 gap-8" : ""}>
          <div className={sidebar ? "lg:col-span-2" : ""}>
            {children}
          </div>
          {sidebar && (
            <aside className="space-y-6">
              {sidebar}
            </aside>
          )}
        </div>

        {fullWidthContent && (
          <div className="mt-8">
            {fullWidthContent}
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}
