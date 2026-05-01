'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import Link from 'next/link';

interface UserProfile {
  id: string;
  email: string;
  name: string | null;
  avatar_url: string | null;
  auth_provider: string;
  role: string;
  created_at: string;
}

interface AnalysisEntry {
  id: string;
  title: string | null;
  created_at: string;
}

export default function ProfileClient() {
  const router = useRouter();
  const t = useTranslations('profile');

  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [name, setName] = useState('');
  const [saveMsg, setSaveMsg] = useState('');

  // RAI Analyst state
  const [inputText, setInputText] = useState('');
  const [analysing, setAnalysing] = useState(false);
  const [analysisError, setAnalysisError] = useState('');
  const [analyses, setAnalyses] = useState<AnalysisEntry[]>([]);

  useEffect(() => {
    fetch('/api/profile')
      .then(r => r.json())
      .then(data => {
        setProfile(data);
        setName(data.name || '');
        setLoading(false);
      });
    fetch('/api/user-analyse')
      .then(r => r.json())
      .then(data => {
        if (Array.isArray(data)) setAnalyses(data);
      });
  }, []);

  async function handleSaveProfile() {
    setSaving(true);
    setSaveMsg('');
    await fetch('/api/profile', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });
    setSaveMsg(t('saved'));
    setSaving(false);
  }

  async function handleSubmitAnalysis() {
    if (inputText.trim().length < 20) return;
    setAnalysing(true);
    setAnalysisError('');
    try {
      const res = await fetch('/api/user-analyse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input_text: inputText }),
      });
      const data = await res.json();
      if (!res.ok) {
        setAnalysisError(data.error || 'Analysis failed');
        return;
      }
      // Redirect to the dedicated analysis page
      router.push(`/analysis/user/${data.id}`);
    } catch {
      setAnalysisError('Network error');
    } finally {
      setAnalysing(false);
    }
  }

  if (loading) {
    return <div className="animate-pulse space-y-6">
      <div className="h-8 w-48 bg-dashboard-border rounded" />
      <div className="h-32 bg-dashboard-surface border border-dashboard-border rounded-lg" />
    </div>;
  }

  const providerLabel = profile?.auth_provider === 'email'
    ? 'Email'
    : profile?.auth_provider
      ? profile.auth_provider.charAt(0).toUpperCase() + profile.auth_provider.slice(1)
      : 'Email';

  return (
    <div className="space-y-8 max-w-3xl">
      {/* Account Section */}
      <section className="bg-dashboard-surface border border-dashboard-border rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4">{t('account')}</h2>
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            {profile?.avatar_url ? (
              <img src={profile.avatar_url} alt="" className="w-14 h-14 rounded-full" />
            ) : (
              <div className="w-14 h-14 rounded-full bg-blue-600 flex items-center justify-center text-white text-xl font-bold">
                {(profile?.name || profile?.email || '?')[0].toUpperCase()}
              </div>
            )}
            <div>
              <p className="text-dashboard-text font-medium">{profile?.email}</p>
              <p className="text-sm text-dashboard-text-muted">
                {t('signedInWith', { provider: providerLabel })}
                {profile?.role === 'admin' && (
                  <span className="ml-2 px-1.5 py-0.5 rounded text-xs bg-purple-500/20 text-purple-300 font-medium">
                    Admin
                  </span>
                )}
              </p>
            </div>
          </div>

          <div>
            <label className="block text-sm text-dashboard-text-muted mb-1">{t('displayName')}</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              className="w-full max-w-sm px-3 py-2 bg-[#141824] border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>
      </section>

      {/* Save name (Focus Country section retired 2026-05-01) */}
      <section className="bg-dashboard-surface border border-dashboard-border rounded-lg p-6">
        <div className="flex items-center gap-3">
          <button
            onClick={handleSaveProfile}
            disabled={saving}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium rounded-lg transition"
          >
            {saving ? t('saving') : t('saveChanges')}
          </button>
          {saveMsg && <span className="text-sm text-green-400">{saveMsg}</span>}
        </div>
      </section>

      {/* RAI Analyst Section */}
      <section className="bg-dashboard-surface border border-dashboard-border rounded-lg p-6">
        <h2 className="text-xl font-bold mb-2">{t('raiAnalyst')}</h2>
        <div className="text-sm text-dashboard-text-muted mb-4 space-y-2">
          <p>{t('raiDescription')}</p>
          <div className="bg-dashboard-border/30 rounded-lg p-3 text-xs space-y-1">
            <p className="font-medium text-dashboard-text">{t('raiExamples')}</p>
            <ul className="list-disc list-inside space-y-0.5 text-dashboard-text-muted">
              <li>{t('raiExample1')}</li>
              <li>{t('raiExample2')}</li>
              <li>{t('raiExample3')}</li>
            </ul>
          </div>
        </div>

        <textarea
          value={inputText}
          onChange={e => setInputText(e.target.value)}
          rows={6}
          maxLength={5000}
          placeholder={t('raiPlaceholder')}
          className="w-full px-3 py-2 bg-[#141824] border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 text-sm resize-y"
        />
        <div className="flex items-center justify-between mt-2">
          <span className="text-xs text-dashboard-text-muted">
            {inputText.length}/5000
          </span>
          <button
            onClick={handleSubmitAnalysis}
            disabled={analysing || inputText.trim().length < 20}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium rounded-lg transition"
          >
            {analysing ? t('analysing') : t('analyse')}
          </button>
        </div>

        {analysisError && (
          <div className="mt-2 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
            {analysisError}
          </div>
        )}

        {/* Analysis History */}
        {analyses.length > 0 && (
          <div className="mt-6">
            <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-3">
              {t('analysisHistory')}
            </h3>
            <div className="space-y-2">
              {analyses.map(a => (
                <Link
                  key={a.id}
                  href={`/analysis/user/${a.id}`}
                  className="flex items-center justify-between px-4 py-3 border border-dashboard-border rounded-lg hover:bg-dashboard-border/30 transition"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-dashboard-text truncate">{a.title}</p>
                    <p className="text-xs text-dashboard-text-muted">
                      {new Date(a.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <svg className="w-4 h-4 text-dashboard-text-muted flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </Link>
              ))}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
