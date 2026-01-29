import { ReactNode } from 'react';
import Logo from './Logo';
import Navigation from './Navigation';
import Footer from './Footer';

interface DashboardLayoutProps {
  children: ReactNode;
  title?: string;
  sidebar?: ReactNode;
  fullWidthContent?: ReactNode;
  // For mobile navigation - pass track context
  centroidLabel?: string;
  centroidId?: string;
  otherTracks?: string[];
  currentTrack?: string;
  currentMonth?: string;
}

export default function DashboardLayout({
  children,
  title,
  sidebar,
  fullWidthContent,
  centroidLabel,
  centroidId,
  otherTracks,
  currentTrack,
  currentMonth
}: DashboardLayoutProps) {
  return (
    <div className="min-h-screen bg-dashboard-surface text-dashboard-text bg-texture-grid">
      <header className="sticky top-0 z-40 border-b border-dashboard-border bg-dashboard-surface/95 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <Logo />
            <Navigation
              centroidLabel={centroidLabel}
              centroidId={centroidId}
              otherTracks={otherTracks}
              currentTrack={currentTrack}
              currentMonth={currentMonth}
            />
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
