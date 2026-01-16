require('dotenv').config({ path: '../apps/frontend/.env.local' });
const { Pool } = require('pg');

const pool = new Pool({
  host: process.env.DB_HOST,
  port: process.env.DB_PORT,
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
});

const descriptions = {
  // Europe
  'EUROPE-NORDIC': 'Denmark, Finland, Iceland, Norway, Sweden, Greenland',
  'EUROPE-BALTIC': 'Estonia, Latvia, Lithuania',
  'EUROPE-BENELUX': 'Belgium, Netherlands, Luxembourg, Ireland',
  'EUROPE-ALPINE': 'Austria, Switzerland, Liechtenstein, Monaco',
  'EUROPE-SOUTH': 'Italy, Spain, Portugal, Greece, Cyprus, Malta',
  'EUROPE-BALKANS': 'Albania, Bosnia, Croatia, Kosovo, Montenegro, North Macedonia, Serbia, Slovenia',
  'EUROPE-BALKANS-EAST': 'Bulgaria, Romania, Moldova',
  'EUROPE-VISEGRAD': 'Poland, Czechia, Slovakia, Hungary',

  // Americas
  'AMERICAS-CENTRAL': 'Belize, Costa Rica, El Salvador, Guatemala, Honduras, Nicaragua, Panama',
  'AMERICAS-CARIBBEAN': 'Island nations and Guianas',
  'AMERICAS-ANDEAN': 'Bolivia, Colombia, Ecuador, Peru',
  'AMERICAS-SOUTHERNCONE': 'Argentina, Chile, Paraguay, Uruguay',

  // Africa
  'AFRICA-WEST': 'Ghana, Ivory Coast, Cameroon, and West African nations',
  'AFRICA-CENTRAL': 'CAR, Congo, Gabon, Angola',
  'AFRICA-EAST': 'Tanzania, Uganda, Rwanda, Kenya region',
  'AFRICA-SOUTHERN': 'Botswana, Namibia, Lesotho, Eswatini',
  'AFRICA-SAHEL': 'Mali, Burkina Faso, Niger, Chad, Mauritania',
  'AFRICA-HORN': 'Somalia, Eritrea, Djibouti, Ethiopia region',

  // Asia
  'ASIA-SOUTHEAST': 'ASEAN nations from Myanmar to Indonesia',
  'ASIA-CENTRAL': 'Kazakhstan, Kyrgyzstan, Tajikistan, Turkmenistan, Uzbekistan',
  'ASIA-SOUTHASIA': 'Afghanistan, Bangladesh, Bhutan, Maldives, Nepal, Pakistan, Sri Lanka',
  'ASIA-CAUCASUS': 'Georgia, Armenia, Azerbaijan',
  'ASIA-HIMALAYA': 'Nepal, Bhutan',

  // Middle East
  'MIDEAST-LEVANT': 'Syria, Jordan, Lebanon, Palestine, Israel region',
  'MIDEAST-MAGHREB': 'Algeria, Libya, Morocco, Mauritania, Tunisia, Western Sahara',
  'MIDEAST-GULF': 'Bahrain, Kuwait, Oman, Qatar, Saudi Arabia, UAE, Yemen region',

  // Oceania
  'OCEANIA-MELANESIA': 'Fiji, New Caledonia, Solomon Islands, Vanuatu',
  'OCEANIA-MICRONESIA': 'FSM, Guam, Kiribati, Marshall Islands, Nauru, Palau',
  'OCEANIA-POLYNESIA': 'Samoa, Tonga, Tuvalu, French Polynesia, Cook Islands',

  // Systemic
  'SYS-CLIMATE': 'Climate change, environment, biodiversity, sustainability',
  'SYS-ENERGY': 'Oil, gas, renewables, energy infrastructure and markets',
  'SYS-FINANCE': 'Banking, debt, monetary policy, financial crises',
  'SYS-HEALTH': 'Pandemics, healthcare systems, global health security',
  'SYS-HUMANITARIAN': 'Displacement, refugees, emergency relief, survival',
  'SYS-TRADE': 'Trade agreements, tariffs, supply chains, WTO',
  'SYS-MILITARY': 'Arms control, military alliances, defense technology',
  'SYS-DIPLOMACY': 'UN, multilateral forums, international law',
  'SYS-TECH': 'AI, cybersecurity, space, emerging technologies',
  'SYS-MEDIA': 'Press freedom, disinformation, media as political actor',

  // Non-State
  'NON-STATE-EU': 'European Union institutions and policy',
  'NON-STATE-NATO': 'NATO operations and expansion',
  'NON-STATE-ISIS': 'Islamic State and affiliates',
  'NON-STATE-AL-QAEDA': 'Al-Qaeda network',
  'NON-STATE-AL-SHAHAAB': 'Al-Shabaab in East Africa',
  'NON-STATE-BOKO-HARAM': 'Boko Haram in West Africa',
  'NON-STATE-KURDISTAN': 'Kurdish political movements',
};

async function populate() {
  console.log('Populating centroid descriptions...\n');

  for (const [id, description] of Object.entries(descriptions)) {
    try {
      const result = await pool.query(
        'UPDATE centroids_v3 SET description = $1 WHERE id = $2 RETURNING id, label',
        [description, id]
      );
      if (result.rows.length > 0) {
        console.log(`✓ ${id}: ${description.substring(0, 50)}...`);
      }
    } catch (err) {
      console.error(`✗ ${id}:`, err.message);
    }
  }

  console.log('\nVerifying...');
  const result = await pool.query(
    'SELECT id, label, description FROM centroids_v3 WHERE description IS NOT NULL ORDER BY id LIMIT 10'
  );

  console.log('\nSample descriptions:');
  result.rows.forEach(r => {
    console.log(`\n${r.label}`);
    console.log(`  ${r.description}`);
  });

  await pool.end();
  console.log('\nDone!');
}

populate().catch(err => {
  console.error('Error:', err);
  pool.end();
});
