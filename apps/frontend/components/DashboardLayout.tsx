import { ReactNode } from 'react';
import Logo from './Logo';
import Link from 'next/link';

interface DashboardLayoutProps {
  children: ReactNode;
  title?: string;
  sidebar?: ReactNode;
}

export default function DashboardLayout({ children, title, sidebar }: DashboardLayoutProps) {
  return (
    <div className="min-h-screen bg-dashboard-bg text-dashboard-text">
      <header className="border-b border-dashboard-border bg-dashboard-surface">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <Logo />
            <nav className="flex gap-6">
              <Link href="/" className="text-dashboard-text-muted hover:text-dashboard-text transition">
                Home
              </Link>
              <Link href="/global" className="text-dashboard-text-muted hover:text-dashboard-text transition">
                Global
              </Link>
            </nav>
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
      </main>
    </div>
  );
}
