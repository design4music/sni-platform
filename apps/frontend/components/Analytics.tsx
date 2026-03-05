'use client';

import { useEffect } from 'react';

const GA_ID = 'G-LF3GZ04SMF';

function getConsent(): string | null {
  const match = document.cookie.match(/cookie_consent=(\w+)/);
  return match ? match[1] : null;
}

function gtag(...args: unknown[]) {
  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push(args);
}

function loadGA4() {
  if (document.querySelector(`script[src*="googletagmanager.com/gtag/js?id=${GA_ID}"]`)) return;

  // Set default consent to denied (cookieless, GDPR-safe)
  gtag('consent', 'default', {
    analytics_storage: 'denied',
  });

  const script = document.createElement('script');
  script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_ID}`;
  script.async = true;
  document.head.appendChild(script);

  gtag('js', new Date());
  gtag('config', GA_ID);

  // If user already accepted, upgrade to full tracking
  if (getConsent() === 'all') {
    gtag('consent', 'update', { analytics_storage: 'granted' });
  }
}

function updateConsent(value: string) {
  gtag('consent', 'update', {
    analytics_storage: value === 'all' ? 'granted' : 'denied',
  });
}

declare global {
  interface Window {
    dataLayer: unknown[];
  }
}

export default function Analytics() {
  useEffect(() => {
    loadGA4();

    function onChange(e: Event) {
      updateConsent((e as CustomEvent).detail);
    }
    window.addEventListener('cookie-consent-changed', onChange);
    return () => window.removeEventListener('cookie-consent-changed', onChange);
  }, []);

  return null;
}
