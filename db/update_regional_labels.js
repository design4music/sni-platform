require('dotenv').config({ path: '../apps/frontend/.env.local' });
const { Pool } = require('pg');

const pool = new Pool({
  host: process.env.DB_HOST,
  port: process.env.DB_PORT,
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
});

const updates = [
  { id: 'EUROPE-SOUTH', label: 'Southern Europe' },
  { id: 'EUROPE-NORDIC', label: 'Nordic Countries' },
  { id: 'EUROPE-BALKANS', label: 'Balkans' },
  { id: 'EUROPE-VISEGRAD', label: 'Visegrad Group' },
  { id: 'AMERICAS-CENTRAL', label: 'Central America' },
  { id: 'AMERICAS-CARIBBEAN', label: 'Caribbean' },
  { id: 'AMERICAS-ANDEAN', label: 'Andean Region' },
  { id: 'AMERICAS-SOUTHERNCONE', label: 'Southern Cone' },
  { id: 'AFRICA-WEST', label: 'West Africa' },
  { id: 'AFRICA-CENTRAL', label: 'Central Africa' },
  { id: 'AFRICA-EAST', label: 'East Africa' },
  { id: 'AFRICA-SOUTHERN', label: 'Southern Africa' },
  { id: 'AFRICA-SAHEL', label: 'Sahel Region' },
  { id: 'AFRICA-HORN', label: 'Horn of Africa' },
  { id: 'ASIA-SOUTHEAST', label: 'Southeast Asia' },
  { id: 'ASIA-CENTRAL', label: 'Central Asia' },
  { id: 'ASIA-SOUTHASIA', label: 'South Asia' },
  { id: 'MIDEAST-LEVANT', label: 'Levant' },
  { id: 'MIDEAST-MAGHREB', label: 'Maghreb' },
  { id: 'MIDEAST-GULF', label: 'Gulf States' },
  { id: 'OCEANIA-MELANESIA', label: 'Melanesia' },
  { id: 'OCEANIA-MICRONESIA', label: 'Micronesia' },
  { id: 'OCEANIA-POLYNESIA', label: 'Polynesia' },
];

async function updateLabels() {
  console.log('Updating regional centroid labels...\n');

  for (const { id, label } of updates) {
    const result = await pool.query(
      'UPDATE centroids_v3 SET label = $1 WHERE id = $2 RETURNING id, label',
      [label, id]
    );
    if (result.rows.length > 0) {
      console.log(`Updated ${id} -> ${label}`);
    }
  }

  console.log('\nVerifying updates...');
  const result = await pool.query(
    `SELECT id, label FROM centroids_v3
     WHERE id = ANY($1)
     ORDER BY label`,
    [updates.map(u => u.id)]
  );

  console.log('\nUpdated centroids:');
  result.rows.forEach(r => console.log(`  ${r.id}: ${r.label}`));

  await pool.end();
  console.log('\nDone!');
}

updateLabels().catch(err => {
  console.error('Error:', err);
  pool.end();
});
