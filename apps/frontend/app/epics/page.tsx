import DashboardLayout from '@/components/DashboardLayout';
import MonthNav from '@/components/MonthNav';
import EpicCard from '@/components/EpicCard';
import { getEpicMonths, getEpicsByMonth } from '@/lib/queries';

export const dynamic = 'force-dynamic';

interface Props {
  searchParams: Promise<{ month?: string }>;
}

export default async function EpicsPage({ searchParams }: Props) {
  const params = await searchParams;
  const months = await getEpicMonths();
  const currentMonth = params.month || months[0] || '';
  const epics = currentMonth ? await getEpicsByMonth(currentMonth) : [];

  const sidebar = months.length > 0 ? (
    <div className="lg:sticky lg:top-24 space-y-6 text-sm">
      <div className="hidden lg:block">
        <MonthNav
          months={months}
          currentMonth={currentMonth}
          baseUrl="/epics"
        />
      </div>

      <div className="hidden lg:block">
        <h3 className="text-lg font-semibold mb-3">About</h3>
        <p className="text-dashboard-text-muted text-sm leading-relaxed">
          Epics are major stories that span multiple countries. They
          are auto-detected from tag co-occurrence patterns across
          countries and regions.
        </p>
      </div>
    </div>
  ) : undefined;

  return (
    <DashboardLayout sidebar={sidebar}>
      <div className="mb-8">
        <h1 className="text-3xl md:text-4xl font-bold mb-2">Cross-Country Epics</h1>
        <p className="text-dashboard-text-muted">
          {currentMonth && `${currentMonth} | `}
          {epics.length} {epics.length === 1 ? 'epic' : 'epics'} detected
        </p>
      </div>

      {/* Mobile month picker */}
      {months.length > 0 && (
        <div className="lg:hidden mb-6">
          <MonthNav
            months={months}
            currentMonth={currentMonth}
            baseUrl="/epics"
          />
        </div>
      )}

      {epics.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {epics.map(epic => (
            <EpicCard key={epic.id} epic={epic} />
          ))}
        </div>
      ) : (
        <div className="text-center py-16">
          <p className="text-dashboard-text-muted text-lg">
            No epics detected for this month.
          </p>
          <p className="text-dashboard-text-muted text-sm mt-2">
            Epics require stories that span at least 8 countries.
          </p>
        </div>
      )}
    </DashboardLayout>
  );
}
