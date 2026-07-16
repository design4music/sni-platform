-- Follow-up correction to 20260716_russia_europe_centroid_widen.sql.
-- AMERICAS-USA is genuinely on-topic for deterrence (US troop posture, nuclear
-- umbrella) but for hybrid_warfare/airspace_incursions it mostly pulled in
-- unrelated Iran/Israel/China/Turkey stories that happen to co-mention the US
-- (a generic-centroid side effect, not a real participant gap) -- audit showed
-- sabotage/espionage/airspace/scramble %foreign roughly doubling after the
-- initial widen. Remove AMERICAS-USA from those two; keep the EUROPE-FRANCE
-- addition (validated: French navy shadow-fleet tanker seizures were genuinely
-- on-topic and had been miscounted as foreign).

UPDATE friction_nodes SET
  centroid_ids = ARRAY['EUROPE-RUSSIA','NON-STATE-EU','NON-STATE-NATO','EUROPE-BALTIC','EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK','EUROPE-VISEGRAD','EUROPE-NORDIC'],
  updated_at = now()
WHERE id IN ('russia_hybrid_warfare', 'russia_airspace_incursions');
