'use client';

import Link from 'next/link';
import { useTranslations } from 'next-intl';

export default function Footer() {
  const currentYear = new Date().getFullYear();
  const t = useTranslations('footer');
  const tNav = useTranslations('nav');

  return (
    <footer className="border-t border-dashboard-border bg-dashboard-surface mt-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* About Section */}
          <div>
            <h3 className="text-lg font-semibold mb-4">WorldBrief</h3>
            <p className="text-dashboard-text-muted text-sm">
              {t('tagline')}
            </p>
          </div>

          {/* Navigation */}
          <div>
            <h3 className="text-lg font-semibold mb-4">{t('navigate')}</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/" className="text-dashboard-text-muted hover:text-dashboard-text transition">
                  {t('home')}
                </Link>
              </li>
              <li>
                <Link href="/trending" className="text-dashboard-text-muted hover:text-dashboard-text transition">
                  {tNav('trending')}
                </Link>
              </li>
              <li>
                <Link href="/signals" className="text-dashboard-text-muted hover:text-dashboard-text transition">
                  {tNav('signals')}
                </Link>
              </li>
              <li>
                <Link href="/epics" className="text-dashboard-text-muted hover:text-dashboard-text transition">
                  {tNav('epics')}
                </Link>
              </li>
              <li>
                <Link href="/sources" className="text-dashboard-text-muted hover:text-dashboard-text transition">
                  {t('sources')}
                </Link>
              </li>
            </ul>
          </div>

          {/* Information */}
          <div>
            <h3 className="text-lg font-semibold mb-4">{t('information')}</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/about" className="text-dashboard-text-muted hover:text-dashboard-text transition">
                  {t('about')}
                </Link>
              </li>
              <li>
                <Link href="/methodology" className="text-dashboard-text-muted hover:text-dashboard-text transition">
                  {t('methodology')}
                </Link>
              </li>
              <li>
                <Link href="/pricing" className="text-dashboard-text-muted hover:text-dashboard-text transition">
                  {tNav('pricing')}
                </Link>
              </li>
              <li>
                <Link href="/faq" className="text-dashboard-text-muted hover:text-dashboard-text transition">
                  {t('faq')}
                </Link>
              </li>
              <li>
                <Link href="/known-issues" className="text-dashboard-text-muted hover:text-dashboard-text transition">
                  {t('knownIssues')}
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className="text-lg font-semibold mb-4">{t('legal')}</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/terms" className="text-dashboard-text-muted hover:text-dashboard-text transition">
                  {t('terms')}
                </Link>
              </li>
              <li>
                <Link href="/privacy" className="text-dashboard-text-muted hover:text-dashboard-text transition">
                  {t('privacy')}
                </Link>
              </li>
              <li>
                <button
                  onClick={() => window.dispatchEvent(new Event('show-cookie-banner'))}
                  className="text-dashboard-text-muted hover:text-dashboard-text transition"
                >
                  {t('cookieSettings')}
                </button>
              </li>
            </ul>
          </div>
        </div>

        {/* Copyright */}
        <div className="mt-8 pt-8 border-t border-dashboard-border">
          <p className="text-sm text-dashboard-text-muted text-center">
            &copy; {currentYear} WorldBrief &{' '}
            <a href="https://www.linkedin.com/in/mmdesign/" target="_blank" rel="noopener noreferrer" className="hover:text-blue-400 transition">
              Maksim Micheliov
            </a>
            . {t('allRights')}
          </p>
        </div>
      </div>
    </footer>
  );
}
