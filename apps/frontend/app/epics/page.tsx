import DashboardLayout from '@/components/DashboardLayout';
import MonthNav from '@/components/MonthNav';
import EpicCard from '@/components/EpicCard';
import SignalSlider from '@/components/SignalSlider';
import { getEpicMonths, getEpicsByMonth, getTopSignalsByMonth } from '@/lib/queries';
import { SignalType } from '@/lib/types';

export const dynamic = 'force-dynamic';

interface Props {
  searchParams: Promise<{ month?: string }>;
}

// Signal grid layout: 2 rows x 3 columns, excluding named_events
const SIGNAL_GRID: { type: SignalType; label: string }[][] = [
  [
    { type: 'persons', label: 'Persons' },
    { type: 'orgs', label: 'Organizations' },
    { type: 'places', label: 'Places' },
  ],
  [
    { type: 'commodities', label: 'Commodities' },
    { type: 'policies', label: 'Policies' },
    { type: 'systems', label: 'Systems' },
  ],
];

function formatMonthName(monthStr: string): string {
  const [year, month] = monthStr.split('-');
  const date = new Date(parseInt(year), parseInt(month) - 1, 1);
  return date.toLocaleDateString('en-US', { month: 'long' });
}

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

      {/* Signal rankings - compact grid */}
      {topSignals && (
        <section id="section-signals">
          <h2 className="text-2xl font-bold mb-4">
            {currentMonth ? `${formatMonthName(currentMonth)} Top 5` : 'Top Signals'}
          </h2>
          <p className="text-dashboard-text-muted text-sm mb-6">
            Most mentioned entities across all headlines this month.
          </p>
          <div className="space-y-4">
            {SIGNAL_GRID.map((row, rowIdx) => (
              <div key={rowIdx} className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {row.map(({ type, label }) => (
                  <SignalSlider
                    key={type}
                    title={label}
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
            No data available for this month.
          </p>
        </div>
      )}
    </DashboardLayout>
  );
}
