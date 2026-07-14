-- Broaden the Arctic environmental narrative to cover climate change (not just
-- drilling recklessness), and make it visible. The atomic is named "Arctic
-- resources competition and climate access", so climate belongs here.
--
-- Paired with a bundle broadening (arctic_resources_competition fn_anchor gains
-- Arctic-climate compound anchors: 'Arctic warming', 'Arctic sea ice', 'black
-- carbon', etc.) so climate-concern titles now match the topic gate at all.
--
-- Also flips arctic_resource_development to framing_required=true so newly-
-- matchable climate titles from business/wire publishers don't misfile as
-- "development" -- the two resource narratives now split by framing keyword,
-- mirroring the corruption 3-stance model.
SET client_encoding TO 'UTF8';

-- 1. development: require a development framing keyword (was publisher-only).
UPDATE narratives_v2
SET framing_required = true,
    updated_at = NOW()
WHERE id = 'arctic_resource_development';

-- 2. environmental narrative: re-scope to warming + environmental harm, broaden
--    framing keywords with climate vocabulary, widen coalition to the cross-bloc
--    outlets that actually report Arctic climate science.
UPDATE narratives_v2
SET name_en = 'Arctic warming and resource extraction are an environmental and climate emergency',
    name_de = 'Arktische Erwärmung und Rohstoffförderung sind ein Umwelt- und Klimanotstand',
    claim_en = 'Environmental-and-climate framing (Western/green press plus climate-science reporting) treats the Arctic as a warning system and a victim: record-low sea ice, accelerating melt and thawing permafrost are a planetary climate signal, while opening the ice to drilling, mining and shipping compounds the damage through oil-spill risk, black carbon and biodiversity loss. It is the pro-development camp''s own critics -- the same outlets that report the resource boom also sound the alarm -- so publisher alone cannot separate the stances; framing keywords do. Vocabulary: record low, warming, melting, thawing permafrost, fragile ecosystem, black carbon, pristine, ban drilling, reckless, climate.',
    claim_de = 'Die Umwelt- und Klima-Rahmung (westliche/grüne Presse und Klimawissenschafts-Berichterstattung) sieht die Arktis als Warnsystem und Opfer: Rekordtief beim Meereis, beschleunigte Schmelze und tauender Permafrost sind ein planetares Klimasignal, während das Öffnen des Eises für Bohrungen, Bergbau und Schifffahrt den Schaden durch Ölpest-Risiko, Ruß und Biodiversitätsverlust vergrößert.',
    stance_label_en = 'Warming & environmental emergency',
    stance_label_de = 'Erwärmung & Umweltnotstand',
    framing_keywords = ARRAY[
      'fragile','ecosystem','climate','environmental','pollution','black carbon',
      'warming','melting','melt','thaw','permafrost','record low','sea ice',
      'ice loss','pristine','biodiversity','ban drilling','reckless','oil spill',
      'protect the Arctic','emissions','carbon',
      'fragiles Ökosystem','Umwelt','Klimaschutz','Klima','Erwärmung','Ölpest',
      'Meereis','Rekordtief','Permafrost'
    ],
    publishers = ARRAY[
      'The Guardian','BBC World','Deutsche Welle','Euronews','France 24 (EN)',
      'New York Times','El País','Le Monde','The Independent','Reuters',
      'Channel NewsAsia','Associated Press','NPR','Al Jazeera'
    ],
    updated_at = NOW()
WHERE id = 'arctic_drilling_environmental_alarm';
