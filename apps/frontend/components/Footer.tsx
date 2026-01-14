import Link from 'next/link';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-dashboard-border bg-dashboard-surface mt-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* About Section */}
          <div>
            <h3 className="text-lg font-semibold mb-4">WorldBrief</h3>
            <p className="text-dashboard-text-muted text-sm">
              Understand the world. Briefly.
            </p>
          </div>

          {/* Navigation */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Navigate</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/" className="text-dashboard-text-muted hover:text-dashboard-text transition">
                  Home
                </Link>
              </li>
              <li>
                <Link href="/global" className="text-dashboard-text-muted hover:text-dashboard-text transition">
                  Global
                </Link>
              </li>
              <li>
                <Link href="/sources" className="text-dashboard-text-muted hover:text-dashboard-text transition">
                  Sources
                </Link>
              </li>
            </ul>
          </div>

          {/* Information */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Information</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/about" className="text-dashboard-text-muted hover:text-dashboard-text transition">
                  About
                </Link>
              </li>
              <li>
                <Link href="/disclaimer" className="text-dashboard-text-muted hover:text-dashboard-text transition">
                  Disclaimer
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Copyright */}
        <div className="mt-8 pt-8 border-t border-dashboard-border">
          <p className="text-sm text-dashboard-text-muted text-center">
            &copy; {currentYear} WorldBrief & Maksim Micheliov. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
