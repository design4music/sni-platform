'use client';

import { useState } from 'react';
import { GeoBriefProfile } from '@/lib/types';

interface GeoBriefSectionProps {
  profile: GeoBriefProfile;
  updatedAt?: Date;
}

function getCountryFlag(iso2?: string): string {
  if (!iso2 || iso2.length !== 2) return '';

  const codePoints = iso2
    .toUpperCase()
    .split('')
    .map(char => 127397 + char.charCodeAt(0));

  return String.fromCodePoint(...codePoints);
}

function AccordionItem({
  section,
  defaultOpen = false
}: {
  section: GeoBriefProfile['sections'][0];
  defaultOpen?: boolean;
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border-b border-dashboard-border last:border-b-0">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between py-4 px-4 text-left bg-dashboard-surface hover:bg-dashboard-surface/80 transition"
        aria-expanded={isOpen}
      >
        <h3 className="text-lg font-semibold">{section.title}</h3>
        <span className="text-dashboard-text-muted text-xl ml-4">
          {isOpen ? '−' : '+'}
        </span>
      </button>

      {isOpen && (
        <div className="px-4 py-6 space-y-4">
          {section.intro && (
            <p className="text-dashboard-text leading-relaxed">{section.intro}</p>
          )}

          {section.bullets && section.bullets.length > 0 && (
            <ul className="space-y-2 ml-4">
              {section.bullets.map((bullet, idx) => (
                <li key={idx} className="text-dashboard-text leading-relaxed list-disc">
                  {bullet}
                </li>
              ))}
            </ul>
          )}

          {section.groups && section.groups.map((group, groupIdx) => (
            <div key={groupIdx} className="space-y-2">
              <h4 className="font-semibold mt-4">{group.title}</h4>
              <ul className="space-y-2 ml-4">
                {group.bullets.map((bullet, bulletIdx) => (
                  <li key={bulletIdx} className="text-dashboard-text leading-relaxed list-disc">
                    {bullet}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function GeoBriefSection({ profile, updatedAt }: GeoBriefSectionProps) {
  if (!profile || profile.schema_version !== 'geo_brief_v0') {
    return null;
  }

  const hasSnapshot = profile.snapshot && profile.snapshot.length > 0;
  const hasSections = profile.sections && profile.sections.length > 0;

  if (!hasSnapshot && !hasSections) {
    return null;
  }

  const flag = getCountryFlag(profile.visuals?.flag_iso2);

  return (
    <div className="border border-dashboard-border rounded-lg overflow-hidden">
      <div className="px-6 py-4 border-b border-dashboard-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-bold">Background Brief</h2>
            {flag && <span className="text-2xl">{flag}</span>}
          </div>
          {updatedAt && (
            <span className="text-sm text-dashboard-text-muted" suppressHydrationWarning>
              Updated {new Date(updatedAt).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}
            </span>
          )}
        </div>
      </div>

      {hasSnapshot && (
        <div className="px-6 py-6 border-b border-dashboard-border">
          <h3 className="text-lg font-semibold mb-4">Snapshot</h3>
          <table className="w-full">
            <tbody>
              {profile.snapshot.map((row, idx) => (
                <tr
                  key={idx}
                  style={idx % 2 === 0 ? { backgroundColor: 'rgba(100, 100, 100, 0.2)' } : {}}
                >
                  <td className="py-3 px-4 text-sm font-medium text-dashboard-text-muted align-top w-1/3">
                    {row.label}
                  </td>
                  <td className="py-3 px-4 text-sm text-dashboard-text leading-relaxed">
                    {row.value}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {hasSections && (
        <div>
          {profile.sections.map((section, idx) => (
            <AccordionItem
              key={section.key || idx}
              section={section}
              defaultOpen={section.default_open}
            />
          ))}
        </div>
      )}

      {profile.footer_note && (
        <div className="px-6 py-4 border-t border-dashboard-border">
          <p className="text-xs text-dashboard-text-muted leading-relaxed">
            {profile.footer_note}
          </p>
        </div>
      )}
    </div>
  );
}
