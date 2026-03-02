'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useTranslations } from 'next-intl';

export default function CookieBanner() {
  const t = useTranslations('cookie');
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!document.cookie.includes('cookie_consent=')) {
      setVisible(true);
    }

    function onShow() {
      setVisible(true);
    }
    window.addEventListener('show-cookie-banner', onShow);
    return () => window.removeEventListener('show-cookie-banner', onShow);
  }, []);

  function setConsent(value: 'all' | 'essential') {
    document.cookie = `cookie_consent=${value}; path=/; max-age=31536000; SameSite=Lax`;
    setVisible(false);
    window.dispatchEvent(new CustomEvent('cookie-consent-changed', { detail: value }));
  }

  if (!visible) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 bg-dashboard-card/95 backdrop-blur-sm border-t border-dashboard-border px-4 py-3">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
        <p className="text-sm text-dashboard-text-muted text-center sm:text-left">
          {t('message')}{' '}
          <Link href="/privacy" className="text-blue-400 hover:text-blue-300 underline">
            {t('privacyPolicy')}
          </Link>
        </p>
        <div className="flex gap-2 shrink-0">
          <button
            onClick={() => setConsent('essential')}
            className="px-4 py-1.5 text-sm font-medium border border-dashboard-border hover:bg-dashboard-surface text-dashboard-text rounded transition"
          >
            {t('essentialOnly')}
          </button>
          <button
            onClick={() => setConsent('all')}
            className="px-4 py-1.5 text-sm font-medium bg-blue-600 hover:bg-blue-500 text-white rounded transition"
          >
            {t('acceptAll')}
          </button>
        </div>
      </div>
    </div>
  );
}
