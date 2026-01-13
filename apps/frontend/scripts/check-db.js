const { Pool } = require('pg');
require('dotenv').config({ path: '.env.local' });

const pool = new Pool({
  host: process.env.DB_HOST,
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
});

async function checkDatabase() {
  try {
    console.log('Checking database connection...');
    const timeResult = await pool.query('SELECT NOW() as time');
    console.log('SUCCESS: Connected to database at', timeResult.rows[0].time);

    console.log('\nChecking tables...');
    const tables = ['centroids_v3', 'ctm', 'titles_v3', 'title_assignments'];

    for (const table of tables) {
      const result = await pool.query(
        `SELECT COUNT(*) as count FROM ${table}`
      );
      console.log(`  ${table}: ${result.rows[0].count} rows`);
    }

    console.log('\nChecking centroid classes...');
    const centroidClasses = await pool.query(
      `SELECT class, COUNT(*) as count FROM centroids_v3 WHERE is_active = true GROUP BY class ORDER BY class`
    );
    centroidClasses.rows.forEach(row => {
      console.log(`  ${row.class}: ${row.count} centroids`);
    });

    console.log('\nChecking tracks...');
    const tracks = await pool.query(
      `SELECT track, COUNT(DISTINCT centroid_id) as centroids, COUNT(*) as ctms
       FROM ctm GROUP BY track ORDER BY track`
    );
    tracks.rows.forEach(row => {
      console.log(`  ${row.track}: ${row.ctms} CTMs across ${row.centroids} centroids`);
    });

    console.log('\nDatabase check complete!');
    process.exit(0);
  } catch (error) {
    console.error('ERROR:', error.message);
    process.exit(1);
  }
}

checkDatabase();
