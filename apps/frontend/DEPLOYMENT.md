# SNI Frontend Deployment Guide

## Prerequisites

- Node.js 18+
- PostgreSQL database with SNI v3 schema
- Environment variables configured

## Environment Variables

Create a `.env.local` file (for local development) or configure in your deployment platform:

```bash
DB_HOST=your_db_host
DB_PORT=5432
DB_NAME=sni_v2
DB_USER=your_db_user
DB_PASSWORD=your_db_password
```

## Local Development

1. Install dependencies:
```bash
npm install
```

2. Run development server:
```bash
npm run dev
```

3. Open http://localhost:3000

## Production Build

```bash
npm run build
npm start
```

The app will run on port 3000 by default.

## Deployment Options

### Vercel (Recommended)

1. Push code to GitHub
2. Import project in Vercel
3. Configure environment variables
4. Deploy

### Docker

Create `Dockerfile`:
```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
```

Build and run:
```bash
docker build -t sni-frontend .
docker run -p 3000:3000 --env-file .env.local sni-frontend
```

### Traditional VPS

1. Install Node.js 18+
2. Clone repository
3. Install dependencies: `npm ci --only=production`
4. Build: `npm run build`
5. Use PM2 or systemd to run: `npm start`

## Database Connection

The app uses PostgreSQL connection pooling via the `pg` library. Ensure:

- Database is accessible from deployment environment
- Firewall rules allow connections
- Connection string is correct
- User has SELECT permissions on tables

## Performance Considerations

- All pages use `force-dynamic` for fresh data
- Database queries use indexes (ensure migrations are run)
- Map loads GeoJSON from CDN (cached by browser)
- No authentication overhead (read-only)

## Monitoring

Check `/api/health` endpoint for database connectivity:
```bash
curl http://localhost:3000/api/health
```

## Troubleshooting

**Database connection fails:**
- Verify environment variables
- Check database accessibility
- Ensure schema is up to date

**Build errors:**
- Clear `.next` folder: `rm -rf .next`
- Reinstall dependencies: `rm -rf node_modules && npm install`
- Check TypeScript errors: `npm run build`

**Map not loading:**
- Check browser console for errors
- Ensure client-side JavaScript is enabled
- Verify GeoJSON CDN is accessible
