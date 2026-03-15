'use client';

import { useState, useCallback } from 'react';
import { useTranslations } from 'next-intl';

interface ExternalLinkProps {
  href: string;
  children: React.ReactNode;
  className?: string;
}

export default function ExternalLink({ href, children, className }: ExternalLinkProps) {
  const t = useTranslations('common');
  const [showConfirm, setShowConfirm] = useState(false);

  const handleClick = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setShowConfirm(true);
  }, []);

  return (
    <>
      <a href={href} onClick={handleClick} className={className}>
        {children}
      </a>
      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={() => setShowConfirm(false)}>
          <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-6 max-w-sm mx-4" onClick={e => e.stopPropagation()}>
            <p className="text-dashboard-text mb-4">{t('leavingConfirm')}</p>
            <p className="text-sm text-dashboard-text-muted mb-4 break-all">{new URL(href).hostname}</p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowConfirm(false)}
                className="px-4 py-2 text-sm text-dashboard-text-muted hover:text-dashboard-text border border-dashboard-border rounded-lg transition"
              >
                {t('cancel')}
              </button>
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
                onClick={() => setShowConfirm(false)}
              >
                {t('continue')}
              </a>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
