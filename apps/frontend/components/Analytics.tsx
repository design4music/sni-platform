'use client';

import { useEffect } from 'react';

const GA_ID = 'G-LF3GZ04SMF';

function getConsent(): string | null {
  const match = document.cookie.match(/cookie_consent=(\w+)/);
  return match ? match[1] : null;
}

function loadGA4() {
  if (document.querySelector(`script[src*="googletagmanager.com/gtag/js?id=${GA_ID}"]`)) return;

  const script = document.createElement('script');
  script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_ID}`;
  script.async = true;
  document.head.appendChild(script);

  window.dataLayer = window.dataLayer || [];
  function gtag(...args: unknown[]) {
    window.dataLayer.push(args);
  }
  gtag('js', new Date());
  gtag('config', GA_ID);
}

function removeGA4() {
  const script = document.querySelector(`script[src*="googletagmanager.com/gtag/js?id=${GA_ID}"]`);
  if (script) script.remove();
  window.dataLayer = [];
}

declare global {
  interface Window {
    dataLayer: unknown[];
  }
}

export default function Analytics() {
  useEffect(() => {
    if (getConsent() === 'all') loadGA4();

    function onChange(e: Event) {
      const detail = (e as CustomEvent).detail;
      if (detail === 'all') {
        loadGA4();
      } else {
        removeGA4();
      }
    }
    window.addEventListener('cookie-consent-changed', onChange);
    return () => window.removeEventListener('cookie-consent-changed', onChange);
  }, []);

  return null;
}
