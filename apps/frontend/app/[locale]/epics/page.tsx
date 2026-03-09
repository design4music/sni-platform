import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';
import MonthNav from '@/components/MonthNav';
import EpicCard from '@/components/EpicCard';
import SignalSlider from '@/components/SignalSlider';
import { getEpicMonths, getEpicsByMonth, getTopSignalsByMonth } from '@/lib/queries';
import { SignalType } from '@/lib/types';
import { setRequestLocale, getTranslations, getLocale } from 'next-intl/server';

export const revalidate = 3600;

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('epics');
  return {
    title: t('title'),
    description: t('metaDescription'),
    alternates: { canonical: '/epics' },
  };
}

interface Props {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ month?: string }>;
}

const SIGNAL_TYPES: { type: SignalType; key: string }[] = [
  { type: 'persons', key: 'persons' },
  { type: 'orgs', key: 'organizations' },
  { type: 'places', key: 'places' },
  { type: 'commodities', key: 'commodities' },
  { type: 'policies', key: 'policies' },
  { type: 'systems', key: 'systems' },
];

function formatMonthName(monthStr: string, loc: string): string {
  const [year, month] = monthStr.split('-');
  const date = new Date(parseInt(year), parseInt(month) - 1, 1);
  return date.toLocaleDateString(loc === 'de' ? 'de-DE' : 'en-US', { month: 'long' });
}

export default async function EpicsPage({ params, searchParams }: Props) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('epics');
  const intlLocale = await getLocale();
  const sp = await searchParams;
  const months = await getEpicMonths();
  const currentMonth = sp.month || months[0] || '';
  const [epics, topSignals] = await Promise.all([
    currentMonth ? getEpicsByMonth(currentMonth, locale) : Promise.resolve([]),
    currentMonth ? getTopSignalsByMonth(currentMonth, 5, locale) : Promise.resolve(null),
  ]);

  // Cap epics at 9 for a clean 3x3 grid
  const displayEpics = epics.slice(0, 9);

  return (
    <DashboardLayout>
      {/* Header with month nav */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl md:text-4xl font-bold mb-1">{t('title')}</h1>
          <p className="text-dashboard-text-muted">
            {currentMonth && `${currentMonth} | `}
            {t('subtitle')}
          </p>
        </div>
        {months.length > 0 && (
          <MonthNav
            months={months}
            currentMonth={currentMonth}
            baseUrl="/epics"
          />
        )}
      </div>

      {/* Epics section */}
      {displayEpics.length > 0 && (
        <section id="section-epics" className="mb-12">
          <h2 className="text-2xl font-bold mb-4">{t('crossCountry')}</h2>
          <p className="text-dashboard-text-muted text-sm mb-6">
            {t('crossCountryDesc')}
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {displayEpics.map(epic => (
              <EpicCard key={epic.id} epic={epic} />
            ))}
          </div>
        </section>
      )}

      {/* Signal rankings - compact grid */}
      {topSignals && (
        <section id="section-signals">
          <h2 className="text-2xl font-bold mb-4">
            {currentMonth ? `${formatMonthName(currentMonth, intlLocale)} ${t('top5')}` : t('topSignals')}
          </h2>
          <p className="text-dashboard-text-muted text-sm mb-6">
            {t('topSignalsDesc')}
          </p>
          <div className="space-y-4">
            {[SIGNAL_TYPES.slice(0, 3), SIGNAL_TYPES.slice(3)].map((row, rowIdx) => (
              <div key={rowIdx} className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {row.map(({ type, key }) => (
                  <SignalSlider
                    key={type}
                    title={t(key)}
                    signals={topSignals[type] || []}
                  />
                ))}
              </div>
            ))}
          </div>
        </section>
      )}

      {!displayEpics.length && !topSignals && (
        <div className="text-center py-16">
          <p className="text-dashboard-text-muted text-lg">
            {t('noData')}
          </p>
        </div>
      )}
    </DashboardLayout>
  );
}
