# SNI Frontend

Strategic Narrative Intelligence frontend application built with Next.js 14.

## Features

- **Dashboard Mode**: Dark theme for navigation pages (home, global, regions, centroids)
- **Reading Mode**: Light theme for CTM narrative content
- **Interactive Map**: Click countries to navigate to centroid pages
- **Cross-Navigation**: Navigate between tracks and centroids via sidebar
- **Month Archives**: Browse historical CTM narratives
- **Typography-First**: Optimized for long-form reading

## Tech Stack

- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- PostgreSQL (via pg)
- Leaflet.js (react-leaflet)

## Setup

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables in `.env.local`:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sni_v2
DB_USER=postgres
DB_PASSWORD=your_password
```

3. Run development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000)

## Navigation Model

- `/` - Home (map, systemic centroids, regions)
- `/global` - All centroids
- `/region/:region_key` - Region directory (centroids only)
- `/c/:centroid_key` - Centroid page (tracks list)
- `/c/:centroid_key/t/:track_key?month=YYYY-MM` - Track page (CTM content)

## Building for Production

```bash
npm run build
npm start
```

## Database Schema

The app reads from these tables:
- `centroids_v3` - Strategic actors and themes
- `ctm` - Centroid-Track-Month aggregations
- `titles_v3` - Source articles
- `title_assignments` - Title-to-CTM mappings

See `db/migrations/` in the root project for schema details.
