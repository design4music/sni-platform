'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { useTranslations } from 'next-intl';
import Link from 'next/link';

interface CentroidOption {
  id: string;
  label: string;
}

interface UserProfile {
  id: string;
  email: string;
  name: string | null;
  avatar_url: string | null;
  auth_provider: string;
  focus_centroid: string | null;
  role: string;
  created_at: string;
}

interface AnalysisEntry {
  id: string;
  title: string | null;
  input_text: string;
  sections: unknown;
  synthesis: string | null;
  created_at: string;
}

interface ProfileClientProps {
  centroidOptions: CentroidOption[];
}

export default function ProfileClient({ centroidOptions }: ProfileClientProps) {
  const { data: session, update: updateSession } = useSession();
  const t = useTranslations('profile');

  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [name, setName] = useState('');
  const [focusCentroid, setFocusCentroid] = useState('');
  const [saveMsg, setSaveMsg] = useState('');

  // RAI Analyst state
  const [inputText, setInputText] = useState('');
  const [analysing, setAnalysing] = useState(false);
  const [analysisError, setAnalysisError] = useState('');
  const [analyses, setAnalyses] = useState<AnalysisEntry[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/profile')
      .then(r => r.json())
      .then(data => {
        setProfile(data);
        setName(data.name || '');
        setFocusCentroid(data.focus_centroid || '');
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
      body: JSON.stringify({ name, focus_centroid: focusCentroid || null }),
    });
    // Trigger session refresh to update JWT with new focus_centroid
    await updateSession();
    setSaveMsg(t('saved'));
    setSaving(false);
    setTimeout(() => setSaveMsg(''), 3000);
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
      // Add to top of list
      setAnalyses(prev => [{
        id: data.id,
        title: inputText.length > 80 ? inputText.slice(0, 77) + '...' : inputText,
        input_text: inputText,
        sections: data.sections,
        synthesis: data.synthesis,
        created_at: new Date().toISOString(),
      }, ...prev]);
      setExpandedId(data.id);
      setInputText('');
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

      {/* Focus Country Section */}
      <section className="bg-dashboard-surface border border-dashboard-border rounded-lg p-6">
        <h2 className="text-xl font-bold mb-2">{t('focusCountry')}</h2>
        <p className="text-sm text-dashboard-text-muted mb-4">
          {t('focusCountryDescription')}
        </p>
        <select
          value={focusCentroid}
          onChange={e => setFocusCentroid(e.target.value)}
          className="w-full max-w-sm px-3 py-2 bg-[#141824] border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
        >
          <option value="">{t('noFocusCountry')}</option>
          {centroidOptions.map(c => (
            <option key={c.id} value={c.id}>{c.label}</option>
          ))}
        </select>

        <div className="mt-4 flex items-center gap-3">
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
                <div key={a.id} className="border border-dashboard-border rounded-lg overflow-hidden">
                  <button
                    onClick={() => setExpandedId(expandedId === a.id ? null : a.id)}
                    className="w-full flex items-center justify-between px-4 py-3 hover:bg-dashboard-border/30 transition text-left"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-dashboard-text truncate">{a.title}</p>
                      <p className="text-xs text-dashboard-text-muted">
                        {new Date(a.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <svg
                      className={`w-4 h-4 text-dashboard-text-muted transition-transform ${expandedId === a.id ? 'rotate-180' : ''}`}
                      fill="none" stroke="currentColor" viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  {expandedId === a.id && (
                    <div className="px-4 pb-4 border-t border-dashboard-border/50">
                      {a.synthesis && (
                        <p className="text-sm text-dashboard-text mt-3 mb-2 italic">{a.synthesis}</p>
                      )}
                      {Array.isArray(a.sections) && a.sections.map((sec: any, i: number) => (
                        <div key={i} className="mt-3">
                          <h4 className="text-sm font-semibold text-dashboard-text">{sec.heading}</h4>
                          {sec.paragraphs?.map((p: string, j: number) => (
                            <p key={j} className="text-sm text-dashboard-text-muted mt-1">{p}</p>
                          ))}
                        </div>
                      ))}
                      <div className="mt-3 pt-2 border-t border-dashboard-border/30">
                        <p className="text-xs text-dashboard-text-muted">{t('originalInput')}:</p>
                        <p className="text-xs text-dashboard-text-muted mt-1 whitespace-pre-wrap">{a.input_text}</p>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
