-- Replace hand-drawn pipeline geometries with real routes from Global Energy
-- Monitor's public GOIT/GGIT pipeline datasets (CC BY 4.0). Coordinates are
-- [longitude, latitude], simplified to <= 80 points and rounded to 3 decimals.
-- Source: greeninfo-network.github.io/global-oil-infrastructure-tracker and
-- greeninfo-network.github.io/global-gas-infrastructure-tracker (GEM GOIT/GGIT
-- dashboards), cross-checked against GlobalEnergyMonitor/goit-ggit-pipeline-routes.

-- Power of Siberia: GEM route (Phase I) from Chinese border crossing near Blagoveshchensk/Heihe northwest into the Yakutia gas fields corridor.
UPDATE strategic_assets
SET geometry = '{"type":"LineString","coordinates":[[127.968,50.237],[127.849,50.737],[127.682,51.231],[127.563,51.646],[127.468,52.058],[127.349,52.494],[127.016,52.697],[126.659,52.826],[126.207,53.07],[125.85,53.241],[125.303,53.61],[124.78,53.722],[123.995,53.779],[122.877,53.961],[122.448,54.282],[120.593,55.661],[120.117,56.008],[119.522,56.458],[118.761,57.019],[118.309,57.367],[117.881,57.673]]}'::jsonb,
    is_active = true,
    meta = COALESCE(meta, '{}'::jsonb) || '{"route_source": "Global Energy Monitor GOIT/GGIT", "route_license": "CC BY 4.0"}'::jsonb
WHERE id = 'power_of_siberia';

-- TurkStream: GEM route from Russkaya compressor station near Anapa across the Black Sea to the landfall near Kiyikoy, Turkey.
UPDATE strategic_assets
SET geometry = '{"type":"LineString","coordinates":[[37.303,44.888],[36.543,44.089],[30.079,42.522],[28.072,41.639],[27.338,41.406],[26.627,40.866],[26.331,40.917]]}'::jsonb,
    is_active = true,
    meta = COALESCE(meta, '{}'::jsonb) || '{"route_source": "Global Energy Monitor GOIT/GGIT", "route_license": "CC BY 4.0"}'::jsonb
WHERE id = 'turkstream';

-- Baku-Tbilisi-Ceyhan: GEM route from Sangachal terminal (Baku) through Georgia and eastern Anatolia to the Ceyhan marine terminal.
UPDATE strategic_assets
SET geometry = '{"type":"LineString","coordinates":[[49.208,40.163],[49.136,40.104],[48.96,40.07],[48.492,40.269],[48.299,40.287],[47.699,40.489],[47.558,40.471],[47.453,40.517],[47.425,40.577],[47.267,40.62],[47.218,40.591],[47.12,40.633],[46.85,40.658],[46.693,40.637],[46.537,40.821],[46.346,40.862],[46.213,40.843],[46.025,40.899],[45.686,41.07],[45.604,41.079],[45.43,41.254],[45.204,41.365],[44.98,41.565],[44.782,41.467],[44.583,41.455],[44.486,41.477],[44.368,41.586],[44.275,41.622],[43.894,41.604],[43.744,41.671],[43.565,41.619],[43.306,41.701],[43.115,41.659],[42.933,41.601],[42.795,41.51],[42.745,41.237],[42.674,41.209],[42.706,41.103],[42.851,40.957],[42.895,40.836],[42.839,40.741],[42.734,40.601],[42.4,40.43],[42.316,40.35],[42.288,40.264],[41.974,40.003],[41.66,39.932],[41.274,39.966],[40.912,39.957],[40.8,39.861],[40.623,39.852],[40.522,39.784],[39.73,39.883],[39.654,39.92],[38.897,39.892],[38.688,39.836],[37.993,39.883],[37.631,39.821],[37.232,39.663],[37.192,39.573],[37.059,39.505],[36.883,39.328],[36.826,39.175],[36.685,39.107],[36.537,38.938],[36.521,38.825],[36.563,38.62],[36.537,38.546],[36.45,38.459],[36.428,38.31],[36.478,38.024],[36.466,37.905],[36.352,37.743],[36.342,37.453],[36.233,37.411],[35.917,37.017],[35.901,36.876]]}'::jsonb,
    is_active = true,
    meta = COALESCE(meta, '{}'::jsonb) || '{"route_source": "Global Energy Monitor GOIT/GGIT", "route_license": "CC BY 4.0"}'::jsonb
WHERE id = 'btc_pipeline';

-- Druzhba (western segment): GEM route chained from Kuibyshev-Unecha-Mozyr-1 -> Mozyr-Brest -> Adamowo-Plock -> Plock-Schwedt sub-segments (Russia -> Belarus -> Poland -> Germany).
UPDATE strategic_assets
SET geometry = '{"type":"LineString","coordinates":[[50.262,52.901],[49.872,52.752],[49.522,52.714],[48.865,52.839],[48.207,52.888],[47.528,52.95],[46.727,52.975],[45.534,53.025],[45.041,53.173],[44.527,53.136],[43.417,53.086],[42.882,53.012],[41.916,52.913],[41.361,52.851],[40.868,52.789],[40.354,52.652],[39.901,52.615],[39.202,52.689],[38.668,52.664],[37.866,52.577],[37.167,52.664],[36.777,52.789],[36.201,52.864],[35.769,52.901],[35.523,52.987],[34.659,52.864],[34.207,52.814],[33.385,52.801],[32.603,52.739],[32.172,52.627],[31.596,52.389],[31.062,52.176],[30.178,51.986],[29.232,51.897],[28.841,51.885],[27.624,52.078],[26.132,52.181],[24.493,52.293],[23.262,52.38],[19.833,52.531],[14.37,53.089]]}'::jsonb,
    is_active = true,
    meta = COALESCE(meta, '{}'::jsonb) || '{"route_source": "Global Energy Monitor GOIT/GGIT", "route_license": "CC BY 4.0"}'::jsonb
WHERE id = 'druzhba_pipeline_west';

-- SUMED: GEM route from Ain Sukhna terminal on the Gulf of Suez to the Sidi Kerir terminal on the Mediterranean, bypassing the Suez Canal.
UPDATE strategic_assets
SET geometry = '{"type":"LineString","coordinates":[[32.349,29.616],[31.904,29.645],[31.849,29.693],[31.608,29.698],[30.454,30.231],[29.778,31.025]]}'::jsonb,
    is_active = true,
    meta = COALESCE(meta, '{}'::jsonb) || '{"route_source": "Global Energy Monitor GOIT/GGIT", "route_license": "CC BY 4.0"}'::jsonb
WHERE id = 'sumed_pipeline';

-- Nord Stream: GEM route from the Vyborg/Portovaya compressor station across the Baltic Sea to the Lubmin landfall near Greifswald, Germany.
UPDATE strategic_assets
SET geometry = '{"type":"LineString","coordinates":[[28.073,60.527],[28.09,60.502],[28.055,60.414],[27.803,60.237],[27.478,60.145],[26.953,60.13],[26.673,60.07],[26.292,60.004],[26.125,59.992],[25.97,59.937],[25.367,59.892],[25.033,59.9],[24.033,59.663],[22.167,59.398],[21.2,59.217],[20.422,58.825],[18.794,56.524],[18.57,56.338],[18.113,56.25],[16.472,55.667],[16.463,55.593],[15.925,55.087],[15.253,54.786],[14.167,54.56],[14.016,54.509],[13.804,54.381],[13.801,54.357],[13.79,54.351],[13.781,54.289],[13.708,54.235],[13.707,54.212],[13.633,54.195],[13.633,54.161],[13.64,54.147]]}'::jsonb,
    is_active = true,
    meta = COALESCE(meta, '{}'::jsonb) || '{"route_source": "Global Energy Monitor GOIT/GGIT", "route_license": "CC BY 4.0"}'::jsonb
WHERE id = 'nord_stream_pipeline';
