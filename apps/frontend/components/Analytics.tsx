'use client';

import { useEffect } from 'react';

const GA_ID = 'G-LF3GZ04SMF';

function getConsent(): string | null {
  const match = document.cookie.match(/cookie_consent=(\w+)/);
  return match ? match[1] : null;
}

// Must push the real `arguments` object, not a spread array --
// gtag.js checks for Arguments, plain arrays are silently ignored.
// eslint-disable-next-line @typescript-eslint/no-unused-vars
function gtag(..._args: unknown[]) {
  window.dataLayer = window.dataLayer || [];
  // eslint-disable-next-line prefer-rest-params
  window.dataLayer.push(arguments);
}

function loadGA4() {
  if (document.querySelector(`script[src*="googletagmanager.com/gtag/js?id=${GA_ID}"]`)) return;

  // Always grant analytics — GDPR consent banner to be re-added later
  gtag('consent', 'default', {
    analytics_storage: 'granted',
  });

  const script = document.createElement('script');
  script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_ID}`;
  script.async = true;
  document.head.appendChild(script);

  gtag('js', new Date());
  gtag('config', GA_ID);
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
