# SNI Frontend - Quick Start Guide

## Prerequisites

- Node.js 18 or higher
- PostgreSQL database with SNI v3 schema
- Database populated with sample data

## Installation

### 1. Navigate to the frontend directory

```bash
cd C:\Users\Maksim\Documents\SNI\apps\frontend
```

### 2. Install dependencies

```bash
npm install
```

This will install all required packages including Next.js, React, TypeScript, Tailwind, pg, and Leaflet.

### 3. Configure environment variables

Copy the database connection details to `.env.local`:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sni_v2
DB_USER=postgres
DB_PASSWORD=your_password_here
```

Replace the values with your actual database credentials.

### 4. Verify database connection

```bash
npm run check-db
```

You should see output like:
```
SUCCESS: Connected to database at 2026-01-13T12:00:00Z

Checking tables...
  centroids_v3: 25 rows
  ctm: 150 rows
  titles_v3: 5000 rows
  title_assignments: 5000 rows

Checking centroid classes...
  geo: 20 centroids
  systemic: 5 centroids

Database check complete!
```

### 5. Start development server

```bash
npm run dev
```

The app will be available at http://localhost:3000

## First Steps

### Verify the Home Page

1. Open http://localhost:3000
2. You should see:
   - SNI logo and navigation
   - Introduction section
   - AI disclaimer
   - Interactive map
   - System centroids cards
   - Region directories

### Test Navigation

1. **Via Map**: Click a highlighted country on the map
   - Should navigate to centroid page
   - Click a track card
   - Should show CTM narrative content

2. **Via Centroids**: Click any centroid card on home page
   - Should show track list
   - Click a track
   - Should show CTM content

3. **Via Regions**: Click a region (e.g., "Europe")
   - Should show centroids in that region
   - Click a centroid
   - Should show tracks

### Check CTM Content

Navigate to a track page (e.g., `/c/UKRAINE/t/military`):

- Should show in Reading Mode (light background)
- Month and article count visible
- Summary text displayed
- Events digest with timeline
- Source articles with links
- Sidebar with:
  - Month archive
  - Other tracks
  - Same track elsewhere

## Common Issues

### Database Connection Failed

```
ERROR: connect ECONNREFUSED
```

**Solution:**
- Verify PostgreSQL is running
- Check DB_HOST, DB_PORT in `.env.local`
- Ensure database allows connections from localhost
- Run `npm run check-db` for detailed error

### No Centroids Showing

**Solution:**
- Run `npm run check-db` to verify data exists
- Check that centroids have `is_active = true`
- Verify database migrations are complete

### Map Not Loading

**Solution:**
- Check browser console for JavaScript errors
- Verify internet connection (GeoJSON loads from CDN)
- Ensure centroids have `iso_codes` populated
- Try refreshing the page

### Build Errors

```
Type error: Cannot find module...
```

**Solution:**
```bash
rm -rf .next
rm -rf node_modules
npm install
npm run build
```

## Production Deployment

### Build for production

```bash
npm run build
```

### Start production server

```bash
npm start
```

Runs on http://localhost:3000 by default.

### Environment variables for production

Set these in your deployment platform:
- DB_HOST
- DB_PORT
- DB_NAME
- DB_USER
- DB_PASSWORD

## Next Steps

### Explore the Codebase

- `app/` - Next.js pages (routing)
- `components/` - React components
- `lib/` - Database queries and utilities

### Read Documentation

- `README.md` - Overview and setup
- `ARCHITECTURE.md` - Design decisions
- `DEPLOYMENT.md` - Deployment options
- `TESTING.md` - Testing checklist
- `PROJECT_SUMMARY.md` - Complete reference

### Customize

1. **Logo**: Edit `components/Logo.tsx`
2. **Colors**: Edit `tailwind.config.ts`
3. **Typography**: Edit `app/globals.css`
4. **Database**: Edit `lib/queries.ts`

## Development Workflow

1. Make changes to code
2. See updates automatically (hot reload)
3. Test in browser
4. Run `npm run build` to verify production build
5. Deploy when ready

## Performance Tips

- Use Chrome DevTools to check page load times
- Monitor database query performance
- Check Network tab for large assets
- Verify SSR is working (view page source)

## Getting Help

1. Check browser console for errors
2. Run `npm run check-db` for database issues
3. Review `TESTING.md` for known issues
4. Check Next.js documentation: https://nextjs.org/docs

## Summary

You now have a fully functional SNI frontend application that:
- Connects to your PostgreSQL database
- Displays centroids and tracks
- Renders CTM narratives
- Provides cross-navigation
- Uses dashboard and reading modes

Navigate to http://localhost:3000 and start exploring!
