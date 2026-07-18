-- Add centroid_ids for global friction node map
-- All new countries, regions, and non-state actors used in the FN taxonomy
-- 2026-06-20

INSERT INTO centroids_v3 (id, label, class, primary_theater, iso_codes) VALUES
-- EUROPE
('EUROPE-ARMENIA', 'Armenia', 'geo', 'caucasus', ARRAY['AM']),
('EUROPE-AZERBAIJAN', 'Azerbaijan', 'geo', 'caucasus', ARRAY['AZ']),
('EUROPE-BOSNIA', 'Bosnia', 'geo', 'balkans', ARRAY['BA']),
('EUROPE-ESTONIA', 'Estonia', 'geo', 'baltics', ARRAY['EE']),
('EUROPE-FINLAND', 'Finland', 'geo', 'nordics', ARRAY['FI']),
('EUROPE-GREENLAND', 'Greenland', 'geo', 'arctic', ARRAY['GL']),
('EUROPE-HUNGARY', 'Hungary', 'geo', 'eu-core', ARRAY['HU']),
('EUROPE-KOSOVO', 'Kosovo', 'geo', 'balkans', ARRAY['XK']),
('EUROPE-LATVIA', 'Latvia', 'geo', 'baltics', ARRAY['LV']),
('EUROPE-LITHUANIA', 'Lithuania', 'geo', 'baltics', ARRAY['LT']),
('EUROPE-SERBIA', 'Serbia', 'geo', 'balkans', ARRAY['RS']),
('EUROPE-SLOVAKIA', 'Slovakia', 'geo', 'eu-core', ARRAY['SK']),
('EUROPE-SWEDEN', 'Sweden', 'geo', 'nordics', ARRAY['SE']),

-- ASIA-PACIFIC
('ASIA-PACIFIC-BHUTAN', 'Bhutan', 'geo', 'south-asia', ARRAY['BT']),
('ASIA-PACIFIC-BRUNEI', 'Brunei', 'geo', 'southeast-asia', ARRAY['BN']),
('ASIA-PACIFIC-FIJI', 'Fiji', 'geo', 'pacific', ARRAY['FJ']),
('ASIA-PACIFIC-INDONESIA', 'Indonesia', 'geo', 'southeast-asia', ARRAY['ID']),
('ASIA-PACIFIC-JAPAN', 'Japan', 'geo', 'east-asia', ARRAY['JP']),
('ASIA-PACIFIC-MALAYSIA', 'Malaysia', 'geo', 'southeast-asia', ARRAY['MY']),
('ASIA-PACIFIC-MYANMAR', 'Myanmar', 'geo', 'southeast-asia', ARRAY['MM']),
('ASIA-PACIFIC-NORTH-KOREA', 'North Korea', 'geo', 'korea', NULL),
('ASIA-PACIFIC-PHILIPPINES', 'Philippines', 'geo', 'southeast-asia', ARRAY['PH']),
('ASIA-PACIFIC-SOLOMON-ISLANDS', 'Solomon Islands', 'geo', 'pacific', ARRAY['SB']),
('ASIA-PACIFIC-SOUTH-KOREA', 'South Korea', 'geo', 'korea', ARRAY['KR']),
('ASIA-PACIFIC-TAIWAN', 'Taiwan', 'geo', 'east-asia', ARRAY['TW']),
('ASIA-PACIFIC-THAILAND', 'Thailand', 'geo', 'southeast-asia', ARRAY['TH']),
('ASIA-PACIFIC-VIETNAM', 'Vietnam', 'geo', 'southeast-asia', ARRAY['VN']),

-- AMERICAS
('AMERICAS-ARGENTINA', 'Argentina', 'geo', 'south-america', ARRAY['AR']),
('AMERICAS-BOLIVIA', 'Bolivia', 'geo', 'south-america', ARRAY['BO']),
('AMERICAS-BRAZIL', 'Brazil', 'geo', 'south-america', ARRAY['BR']),
('AMERICAS-CANADA', 'Canada', 'geo', 'north-america', ARRAY['CA']),
('AMERICAS-CENTRAL-AMERICA', 'Central America', 'geo', 'central-america', ARRAY['GT','HN','SV','NI','CR','PA']),
('AMERICAS-CHILE', 'Chile', 'geo', 'south-america', ARRAY['CL']),
('AMERICAS-COLOMBIA', 'Colombia', 'geo', 'south-america', ARRAY['CO']),
('AMERICAS-CUBA', 'Cuba', 'geo', 'caribbean', ARRAY['CU']),
('AMERICAS-GUYANA', 'Guyana', 'geo', 'south-america', ARRAY['GY']),
('AMERICAS-PERU', 'Peru', 'geo', 'south-america', ARRAY['PE']),
('AMERICAS-VENEZUELA', 'Venezuela', 'geo', 'south-america', ARRAY['VE']),

-- AFRICA
('AFRICA-ANGOLA', 'Angola', 'geo', 'sub-saharan', ARRAY['AO']),
('AFRICA-BURKINA-FASO', 'Burkina Faso', 'geo', 'sahel', ARRAY['BF']),
('AFRICA-BURUNDI', 'Burundi', 'geo', 'great-lakes', ARRAY['BI']),
('AFRICA-DJIBOUTI', 'Djibouti', 'geo', 'horn', ARRAY['DJ']),
('AFRICA-ERITREA', 'Eritrea', 'geo', 'horn', ARRAY['ER']),
('AFRICA-ETHIOPIA', 'Ethiopia', 'geo', 'horn', ARRAY['ET']),
('AFRICA-KENYA', 'Kenya', 'geo', 'horn', ARRAY['KE']),
('AFRICA-MALI', 'Mali', 'geo', 'sahel', ARRAY['ML']),
('AFRICA-MAURITANIA', 'Mauritania', 'geo', 'sahel', ARRAY['MR']),
('AFRICA-NIGER', 'Niger', 'geo', 'sahel', ARRAY['NE']),
('AFRICA-NIGERIA', 'Nigeria', 'geo', 'sahel', ARRAY['NG']),
('AFRICA-RWANDA', 'Rwanda', 'geo', 'great-lakes', ARRAY['RW']),
('AFRICA-SOMALIA', 'Somalia', 'geo', 'horn', ARRAY['SO']),
('AFRICA-SUDAN', 'Sudan', 'geo', 'horn', ARRAY['SD']),
('AFRICA-UGANDA', 'Uganda', 'geo', 'great-lakes', ARRAY['UG']),
('AFRICA-DRC', 'Democratic Republic of Congo', 'geo', 'great-lakes', ARRAY['CD']),

-- MIDEAST (regional/multi-country centroids)
('MIDEAST-GULF', 'Persian Gulf States', 'geo', 'gulf', ARRAY['AE','BH','KW','OM','QA']),
('MIDEAST-LEVANT', 'Levant Region', 'geo', 'levant', ARRAY['SY','LB','JO','PS']),
('MIDEAST-SAUDI', 'Saudi Arabia', 'geo', 'gulf', ARRAY['SA']),

-- NON-STATE ACTORS
('NON-STATE-AL-QAEDA', 'Al-Qaeda', 'systemic', NULL, NULL),
('NON-STATE-AL-SHABAAB', 'Al-Shabaab', 'systemic', NULL, NULL),
('NON-STATE-ANTI-JUNTA', 'Myanmar Anti-Junta Groups', 'systemic', NULL, NULL),
('NON-STATE-CARTELS', 'Drug Cartels', 'systemic', NULL, NULL),
('NON-STATE-ETHNIC-MILITIAS', 'Ethnic Armed Militias', 'systemic', NULL, NULL),
('NON-STATE-JIHADISTS', 'Jihadist Groups', 'systemic', NULL, NULL),
('NON-STATE-M23', 'M23 Rebel Group', 'systemic', NULL, NULL),
('NON-STATE-OROMIA-LIBERATION-FRONT', 'Oromo Liberation Front', 'systemic', NULL, NULL)

ON CONFLICT (id) DO NOTHING;
