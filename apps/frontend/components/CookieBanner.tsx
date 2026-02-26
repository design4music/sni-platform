'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

export default function CookieBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!document.cookie.includes('cookie_consent=1')) {
      setVisible(true);
    }
  }, []);

  function accept() {
    document.cookie = 'cookie_consent=1; path=/; max-age=31536000; SameSite=Lax';
    setVisible(false);
  }

  if (!visible) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 bg-dashboard-card/95 backdrop-blur-sm border-t border-dashboard-border px-4 py-3">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
        <p className="text-sm text-dashboard-text-muted text-center sm:text-left">
          This site uses cookies for authentication and analytics.{' '}
          <Link href="/privacy" className="text-blue-400 hover:text-blue-300 underline">
            Privacy Policy
          </Link>
        </p>
        <button
          onClick={accept}
          className="shrink-0 px-4 py-1.5 text-sm font-medium bg-blue-600 hover:bg-blue-500 text-white rounded transition"
        >
          Got it
        </button>
      </div>
    </div>
  );
}
