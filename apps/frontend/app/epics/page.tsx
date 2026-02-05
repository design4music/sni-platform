import DashboardLayout from '@/components/DashboardLayout';
import MonthNav from '@/components/MonthNav';
import EpicCard from '@/components/EpicCard';
import SignalCard from '@/components/SignalCard';
import { getEpicMonths, getEpicsByMonth, getTopSignalsByMonth } from '@/lib/queries';
import { SignalType, SIGNAL_LABELS } from '@/lib/types';

export const dynamic = 'force-dynamic';

interface Props {
  searchParams: Promise<{ month?: string }>;
}

const SIGNAL_ORDER: SignalType[] = [
  'persons', 'orgs', 'places', 'commodities',
  'policies', 'systems', 'named_events',
];

export default async function EpicsPage({ searchParams }: Props) {
  const params = await searchParams;
  const months = await getEpicMonths();
  const currentMonth = params.month || months[0] || '';
  const [epics, topSignals] = await Promise.all([
    currentMonth ? getEpicsByMonth(currentMonth) : Promise.resolve([]),
    currentMonth ? getTopSignalsByMonth(currentMonth) : Promise.resolve(null),
  ]);

  // Cap epics at 9 for a clean 3x3 grid
  const displayEpics = epics.slice(0, 9);

  return (
    <DashboardLayout>
      {/* Header with month nav */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl md:text-4xl font-bold mb-1">Monthly Intelligence</h1>
          <p className="text-dashboard-text-muted">
            {currentMonth && `${currentMonth} | `}
            Cross-country epics and signal rankings
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
          <h2 className="text-2xl font-bold mb-4">Cross-Country Epics</h2>
          <p className="text-dashboard-text-muted text-sm mb-6">
            Major stories spanning multiple countries, auto-detected from tag co-occurrence patterns.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {displayEpics.map(epic => (
              <EpicCard key={epic.id} epic={epic} />
            ))}
          </div>
        </section>
      )}

      {/* Signal rankings */}
      {topSignals && (
        <section id="section-signals" className="space-y-10">
          {SIGNAL_ORDER.map(signalType => {
            const items = topSignals[signalType];
            if (!items || items.length === 0) return null;
            return (
              <div key={signalType} id={`section-${signalType}`}>
                <h2 className="text-xl font-bold mb-4">
                  {SIGNAL_LABELS[signalType]}
                </h2>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                  {items.map((item, i) => (
                    <SignalCard key={item.value} signal={item} rank={i} />
                  ))}
                </div>
              </div>
            );
          })}
        </section>
      )}

      {!displayEpics.length && !topSignals && (
        <div className="text-center py-16">
          <p className="text-dashboard-text-muted text-lg">
            No data available for this month.
          </p>
        </div>
      )}
    </DashboardLayout>
  );
}
