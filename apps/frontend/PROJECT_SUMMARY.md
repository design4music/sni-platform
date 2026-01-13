# SNI Frontend - Project Summary

## Overview

The SNI (Strategic Narrative Intelligence) frontend is a professional web application for navigating AI-generated global news narratives. It presents strategic intelligence organized by actors (centroids) and thematic domains (tracks).

## Project Location

```
C:\Users\Maksim\Documents\SNI\apps\frontend
```

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Database**: PostgreSQL (read-only via pg)
- **Maps**: Leaflet.js (react-leaflet)
- **Runtime**: Node.js 18+

## Project Structure

```
apps/frontend/
├── app/                          # Next.js App Router pages
│   ├── layout.tsx               # Root layout
│   ├── page.tsx                 # Home page
│   ├── globals.css              # Global styles
│   ├── loading.tsx              # Loading state
│   ├── error.tsx                # Error boundary
│   ├── not-found.tsx            # 404 page
│   ├── global/
│   │   └── page.tsx             # Global centroids page
│   ├── region/
│   │   └── [region_key]/
│   │       └── page.tsx         # Region directory page
│   ├── c/
│   │   └── [centroid_key]/
│   │       ├── page.tsx         # Centroid page
│   │       └── t/
│   │           └── [track_key]/
│   │               └── page.tsx # Track page (CTM content)
│   └── api/
│       └── health/
│           └── route.ts         # Health check endpoint
├── components/                   # React components
│   ├── Logo.tsx
│   ├── DashboardLayout.tsx      # Dark theme layout
│   ├── ReadingLayout.tsx        # Light theme layout
│   ├── CentroidCard.tsx
│   ├── TrackCard.tsx
│   ├── WorldMap.tsx             # Interactive Leaflet map
│   └── EmptyState.tsx
├── lib/                         # Core utilities
│   ├── db.ts                    # Database connection pool
│   ├── queries.ts               # Database query functions
│   ├── types.ts                 # TypeScript types
│   └── utils.ts                 # Helper functions
├── scripts/
│   └── check-db.js              # Database health check
├── public/                      # Static assets
├── .env.local                   # Environment variables (local)
├── next.config.js               # Next.js configuration
├── tailwind.config.ts           # Tailwind configuration
├── tsconfig.json                # TypeScript configuration
├── package.json                 # Dependencies and scripts
├── README.md                    # Quick start guide
├── DEPLOYMENT.md                # Deployment instructions
├── ARCHITECTURE.md              # Architecture documentation
├── TESTING.md                   # Testing checklist
└── PROJECT_SUMMARY.md           # This file
```

## Key Features

### 1. Navigation Model
- **Home** (`/`): Map, system centroids, regions
- **Global** (`/global`): All centroids list
- **Region** (`/region/:key`): Regional centroids
- **Centroid** (`/c/:key`): Track list
- **Track** (`/c/:key/t/:track`): CTM narrative content

### 2. Design Modes
- **Dashboard Mode**: Dark theme for navigation
- **Reading Mode**: Light theme for CTM content

### 3. Interactive Map
- GeoJSON country polygons (no tiles)
- Highlight countries by ISO codes
- Click navigation to centroids

### 4. Cross-Navigation
- Month archives (historical CTMs)
- Other tracks for same centroid
- Same track on other centroids

## Database Schema

### Tables Used
- `centroids_v3`: Centroids (geo/systemic actors)
- `ctm`: Centroid-Track-Month aggregations
- `titles_v3`: Source articles
- `title_assignments`: Title-CTM relationships

### Key Columns
- `centroids_v3.iso_codes`: For map highlighting
- `ctm.events_digest`: JSONB array of events
- `ctm.summary_text`: Monthly narrative summary
- `ctm.month`: Date (YYYY-MM-01 format)

## Commands

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Check database connectivity
npm run check-db

# Lint code
npm run lint
```

## Environment Variables

Required in `.env.local`:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sni_v2
DB_USER=postgres
DB_PASSWORD=your_password
```

## API Endpoints

### `/api/health`
Returns database connectivity status:
```json
{
  "status": "ok",
  "database": "connected",
  "timestamp": "2026-01-13T12:00:00Z"
}
```

## Typography System

### Dashboard Mode
- Background: `#0a0e1a` (very dark blue)
- Surface: `#111827` (dark gray)
- Text: `#f9fafb` (light gray)

### Reading Mode
- Background: `#ffffff` (white)
- Surface: `#f9fafb` (light gray)
- Text: `#111827` (dark gray)

### Font Stack
- Sans: Inter, system-ui, sans-serif
- Serif: Georgia, serif (for reading content)

## Design Principles

1. **Centroid-First**: All content revolves around centroids
2. **2-Click Rule**: CTM content in ≤2 clicks from home
3. **Typography-First**: Reading experience paramount
4. **No Empty Pages**: Every page has clear purpose
5. **Credible Intelligence**: Professional, restrained design

## Performance

- **SSR**: All pages server-rendered for fresh data
- **Connection Pooling**: Efficient database usage
- **Indexed Queries**: Fast lookups on centroid, track, month
- **No Auth Overhead**: Read-only, no sessions
- **Minimal JS**: Server components reduce bundle size

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- No IE11

## Deployment

### Recommended: Vercel
1. Push to GitHub
2. Import in Vercel
3. Set environment variables
4. Deploy

### Alternative: Docker
```bash
docker build -t sni-frontend .
docker run -p 3000:3000 --env-file .env.local sni-frontend
```

### Alternative: VPS
```bash
npm ci --only=production
npm run build
npm start
```

## Development Workflow

1. **Start dev server**: `npm run dev`
2. **Check database**: `npm run check-db`
3. **Make changes**: Edit files in `app/` or `components/`
4. **Test locally**: Navigate to http://localhost:3000
5. **Build**: `npm run build`
6. **Deploy**: Push to deployment platform

## Testing

See `TESTING.md` for comprehensive checklist covering:
- All page routes
- Navigation flows
- Database queries
- Error handling
- Typography rendering
- Map interactions

## Future Enhancements

### Phase 1 (Quick Wins)
- Search functionality
- Activity indicators
- Sort/filter options

### Phase 2 (Moderate)
- User preferences
- RSS feeds
- PDF export

### Phase 3 (Advanced)
- Comparative views
- Timeline visualizations
- Entity graphs

## Known Limitations

- JavaScript required (map, client components)
- No offline support
- Real-time updates require refresh
- Desktop-first (mobile responsive but not optimized)

## Security

- Read-only database access
- No user authentication
- Environment variables for credentials
- React auto-escaping (XSS protection)
- Connection pooling (DoS mitigation)

## Support

For issues or questions:
1. Check `TESTING.md` for known issues
2. Verify database connectivity with `npm run check-db`
3. Review `ARCHITECTURE.md` for design decisions
4. Check browser console for errors

## License

Internal use only (SNI project)

## Contributors

- Built according to SNI frontend specification
- Following SNI v3 backend schema
- Optimized for strategic intelligence presentation
