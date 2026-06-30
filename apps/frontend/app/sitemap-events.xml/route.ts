export const dynamic = 'force-dynamic';

const SITE_URL = 'https://www.worldbrief.info';

// Legacy query-param URLs — redirect to path-based equivalents.
export async function GET(request: Request) {
  const month = new URL(request.url).searchParams.get('month');
  if (!month || !/^\d{4}-\d{2}$/.test(month)) {
    return new Response('Pass ?month=YYYY-MM', { status: 400 });
  }
  return Response.redirect(`${SITE_URL}/sitemaps/events-${month}.xml`, 301);
}
