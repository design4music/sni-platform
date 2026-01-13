# SNI Frontend Architecture

## Design Philosophy

The SNI frontend follows these core principles:

1. **Centroid-First Navigation**: All content revolves around centroids (actors/themes)
2. **Minimal Click Depth**: Users reach CTM content in 2 clicks max from home
3. **Typography-First Design**: Reading experience is paramount
4. **Dashboard vs Reading Modes**: Clear visual distinction between navigation and content
5. **Server-Side Rendering**: Fresh data on every page load (no stale cache)

## Navigation Model

```
/ (Home)
├── /global (All centroids)
├── /region/:region_key (Region directory)
│   └── /c/:centroid_key (Centroid page)
│       └── /c/:centroid_key/t/:track_key (Track page with CTM)
└── Direct map navigation to /c/:centroid_key
```

### Page Responsibilities

- **Home**: Entry point, map, system centroids, regions
- **Global**: Comprehensive centroid list
- **Region**: Geographic centroids in a region (NO CTMs)
- **Centroid**: Track list for a centroid (NO CTM content)
- **Track**: CTM narrative content (summary, events, titles)

## Data Flow

```
PostgreSQL Database
    ↓
lib/queries.ts (Server-side queries)
    ↓
app/*/page.tsx (Server Components)
    ↓
components/* (React Components)
    ↓
Browser
```

### Key Database Tables

- `centroids_v3`: Strategic actors and thematic lenses
- `ctm`: Centroid-Track-Month aggregations (narratives)
- `titles_v3`: Source articles
- `title_assignments`: Many-to-many title-CTM relationships

## Component Structure

### Layouts

- **DashboardLayout**: Dark theme for navigation pages
- **ReadingLayout**: Light theme for CTM content pages

### Cards

- **CentroidCard**: Clickable centroid with label and type
- **TrackCard**: Track entry with latest month and article count

### Map

- **WorldMap**: Interactive Leaflet map with GeoJSON polygons
- Highlights countries by ISO codes from database
- Click navigation to centroid pages

## Styling System

### Color Tokens

```typescript
dashboard: {
  bg: '#0a0e1a',        // Dark background
  surface: '#111827',   // Card background
  border: '#1f2937',    // Borders
  text: '#f9fafb',      // Primary text
  text-muted: '#9ca3af' // Secondary text
}

reading: {
  bg: '#ffffff',        // Light background
  surface: '#f9fafb',   // Card background
  border: '#e5e7eb',    // Borders
  text: '#111827',      // Primary text
  text-muted: '#6b7280' // Secondary text
}
```

### Typography Hierarchy

- **H1**: 4xl, bold - Page titles
- **H2**: 3xl, bold - Section titles
- **H3**: 2xl, semibold - Subsections
- **Body**: lg, relaxed - Reading content
- **Small**: sm, muted - Metadata

## Performance Considerations

### Server Components

All pages use Next.js Server Components for:
- Direct database access (no API layer)
- SEO-friendly rendering
- Reduced client bundle size

### Dynamic Rendering

```typescript
export const dynamic = 'force-dynamic';
```

This ensures fresh data on every request. Future optimization could add:
- ISR (Incremental Static Regeneration) for frozen CTMs
- Client-side caching for navigation

### Database Queries

- Indexed queries on `centroid_id`, `track`, `month`
- Connection pooling via `pg` library
- Read-only operations (no write overhead)

## Cross-Navigation

### Sidebar Components

Track pages include sidebars with:
1. **Month Archive**: Historical CTMs for same centroid-track
2. **Other Tracks**: Different tracks for same centroid
3. **Same Track Elsewhere**: Same track on other centroids

This creates a web of interconnected narratives.

## Future Enhancements

### Phase 1 (Easy Wins)
- Search functionality
- Activity indicators (recent updates)
- Sort/filter options in centroid lists

### Phase 2 (Moderate Effort)
- User preferences (track favorites)
- RSS feeds for centroid-track combinations
- Export CTM as PDF

### Phase 3 (Advanced Features)
- Comparative views (multiple centroids side-by-side)
- Timeline visualizations
- Entity relationship graphs

## Error Handling

- **404**: Custom not-found page for missing routes
- **500**: Error boundary with retry option
- **Database errors**: Graceful fallback with error message
- **Loading states**: Skeleton screens for async operations

## Accessibility

- Semantic HTML structure
- ARIA labels where appropriate
- Keyboard navigation support
- High contrast ratios (WCAG AA compliant)

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- JavaScript required (map, client components)
- No IE11 support

## Security

- Read-only database access
- No user authentication (no session management)
- No XSS vectors (React auto-escaping)
- Environment variables for sensitive data
- PostgreSQL connection pooling (prevents exhaustion)
