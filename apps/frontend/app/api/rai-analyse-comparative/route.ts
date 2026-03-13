export const maxDuration = 180;

import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/auth';
import { query } from '@/lib/db';
import {
  buildComparativePrompt,
  buildUnifiedComparativePrompt,
  callDeepSeek,
  parseAnalysisResponse,
  parseComparativeScores,
  selectModulesByLabels,
  resolveModules,
} from '@/lib/rai-engine';
import type { ClusterNarrative, AnalysisContext, CentroidTimeline } from '@/lib/rai-engine';
import type { SignalStats } from '@/lib/types';
import { getCentroidTimeline } from '@/lib/queries';

async function handleSiblingGroup(siblingGroupId: string) {
  const t0 = Date.now();
  const lap = (label: string) => console.log(`[sibling-analysis] ${label}: ${Date.now() - t0}ms`);
  // Check cache first
  const cached = await query<{
    sections: string | null;
    scores: unknown;
    synthesis: string | null;
    blind_spots: string[] | null;
    conflicts: string[] | null;
  }>(
    `SELECT sections, scores, synthesis, blind_spots, conflicts
     FROM entity_analyses
     WHERE entity_type = 'sibling_group' AND entity_id = $1`,
    [siblingGroupId]
  );
  if (cached.length > 0 && cached[0].sections) {
    let sections = cached[0].sections;
    if (typeof sections === 'string') {
      try { sections = JSON.parse(sections); } catch { /* use as-is */ }
    }
    return NextResponse.json({
      sections,
      scores: cached[0].scores,
      synthesis: cached[0].synthesis,
      blind_spots: cached[0].blind_spots,
      conflicts: cached[0].conflicts,
    });
  }

  lap('cache-check');
  // Fetch all sibling events
  const siblingRows = await query<{
    event_id: string;
    event_title: string;
    source_count: number;
    centroid_id: string;
    centroid_name: string;
    track: string;
    event_date: string;
  }>(
    `SELECT e.id as event_id,
            COALESCE(e.title, e.topic_core) as event_title,
            e.source_batch_count as source_count,
            ctm.centroid_id, cv.label as centroid_name, ctm.track,
            e.date::text as event_date
     FROM events_v3 e
     JOIN ctm ON ctm.id = e.ctm_id
     JOIN centroids_v3 cv ON cv.id = ctm.centroid_id
     WHERE e.sibling_group = $1
     ORDER BY e.source_batch_count DESC`,
    [siblingGroupId]
  );

  if (siblingRows.length < 2) {
    return NextResponse.json(
      { error: 'Sibling group not found or has fewer than 2 events' },
      { status: 404 }
    );
  }

  // Fetch narratives for all sibling events grouped by centroid
  const eventIds = siblingRows.map((r) => r.event_id);
  const narrativeRows = await query<{
    entity_id: string;
    label: string;
    description: string | null;
    moral_frame: string | null;
    sample_titles: unknown;
    title_count: number;
    cluster_label: string;
    cluster_publishers: string[];
    cluster_score_avg: number;
    signal_stats: SignalStats | null;
  }>(
    `SELECT n.entity_id, n.label, n.description, n.moral_frame, n.sample_titles,
            n.title_count, n.cluster_label, n.cluster_publishers,
            n.cluster_score_avg, n.signal_stats
     FROM narratives n
     WHERE n.entity_type = 'event'
       AND n.entity_id = ANY($1::uuid[])
       AND n.extraction_method = 'stance_clustered'
     ORDER BY n.cluster_score_avg ASC`,
    [eventIds]
  );

  if (narrativeRows.length === 0) {
    return NextResponse.json(
      { error: 'No stance-clustered narratives found for sibling events.' },
      { status: 404 }
    );
  }

  // Build centroid-keyed map
  const eventToCentroid = new Map<string, string>();
  for (const r of siblingRows) {
    eventToCentroid.set(r.event_id, r.centroid_name);
  }

  const narrativesByCentroid = new Map<string, ClusterNarrative[]>();
  const allNarratives: ClusterNarrative[] = [];

  for (const r of narrativeRows) {
    const centroidName = eventToCentroid.get(r.entity_id) || 'Unknown';
    const cn: ClusterNarrative = {
      cluster_label: r.cluster_label || 'unknown',
      cluster_publishers: r.cluster_publishers || [],
      cluster_score_avg: r.cluster_score_avg || 0,
      label: r.label,
      description: r.description,
      moral_frame: r.moral_frame,
      sample_titles: typeof r.sample_titles === 'string'
        ? JSON.parse(r.sample_titles)
        : r.sample_titles || [],
      title_count: r.title_count,
      centroid_name: centroidName,
    };

    if (!narrativesByCentroid.has(centroidName)) {
      narrativesByCentroid.set(centroidName, []);
    }
    narrativesByCentroid.get(centroidName)!.push(cn);
    allNarratives.push(cn);
  }

  // Use first event's context for module selection
  const context: AnalysisContext = {
    centroid_id: siblingRows[0].centroid_id,
    centroid_name: siblingRows[0].centroid_name,
    track: siblingRows[0].track,
    event_title: siblingRows[0].event_title,
    entity_type: 'sibling_group',
  };

  lap('narratives-fetched');
  // Select modules deterministically (no LLM selector call needed)
  const moduleIds = selectModulesByLabels(null);
  const modules = resolveModules(moduleIds);
  lap('modules-resolved');

  // Collect unique tags from all sibling events for relevance scoring
  const siblingEventTags = await query<{ tag: string }>(
    `SELECT DISTINCT unnest(COALESCE(tags, ARRAY[]::text[])) as tag
     FROM events_v3 WHERE sibling_group = $1 AND tags IS NOT NULL`,
    [siblingGroupId]
  ).then((rows) => rows.map((r) => r.tag));

  // Use earliest sibling event date as timeline anchor (no future events)
  const earliestDate = siblingRows
    .map((r) => r.event_date)
    .sort()[0];

  const uniqueCentroids = [...new Set(siblingRows.map((r) => r.centroid_id))];
  const timelines: CentroidTimeline[] = await Promise.all(
    uniqueCentroids.map(async (centroidId) => {
      const centroidName = siblingRows.find((r) => r.centroid_id === centroidId)!.centroid_name;
      // Fewer events per centroid when many centroids to keep prompt manageable
      const perCentroidLimit = uniqueCentroids.length >= 4 ? 5 : uniqueCentroids.length >= 3 ? 7 : 12;
      // Boost bilateral events that reference sibling centroids
      const siblingCentroidIds = uniqueCentroids.filter((c) => c !== centroidId);
      const events = await getCentroidTimeline(
        centroidId,
        eventIds,
        siblingEventTags,
        90,
        perCentroidLimit,
        siblingCentroidIds,
        earliestDate,
      );
      return { centroid_name: centroidName, events };
    })
  );
  const nonEmptyTimelines = timelines.filter((t) => t.events.length > 0);

  lap('timelines-fetched');
  // Build unified prompt
  const prompt = buildUnifiedComparativePrompt(
    narrativesByCentroid,
    siblingRows.map((r) => ({
      centroid_name: r.centroid_name,
      event_title: r.event_title,
      source_count: r.source_count,
    })),
    modules,
    null,
    nonEmptyTimelines,
  );
  console.log(`[sibling-analysis] prompt length: ${prompt.length} chars`);
  const raw = await callDeepSeek(prompt, 6000);
  lap('deepseek-done');
  const { sections } = parseAnalysisResponse(raw);
  const scores = parseComparativeScores(raw);

  if (sections.length === 0) {
    console.error('DeepSeek returned no parseable sections for unified analysis');
    return NextResponse.json({ error: 'Analysis returned no content' }, { status: 502 });
  }

  // Save to entity_analyses
  await query(
    `INSERT INTO entity_analyses
       (entity_type, entity_id, cluster_count, sections, scores,
        synthesis, blind_spots, conflicts)
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
     ON CONFLICT (entity_type, entity_id) DO UPDATE SET
       cluster_count = EXCLUDED.cluster_count,
       sections = EXCLUDED.sections,
       scores = EXCLUDED.scores,
       synthesis = EXCLUDED.synthesis,
       blind_spots = EXCLUDED.blind_spots,
       conflicts = EXCLUDED.conflicts,
       created_at = NOW()`,
    [
      'sibling_group',
      siblingGroupId,
      allNarratives.length,
      JSON.stringify(sections),
      JSON.stringify(scores),
      scores.synthesis || null,
      scores.collective_blind_spots?.length ? scores.collective_blind_spots : null,
      null,
    ]
  );

  return NextResponse.json({
    sections,
    scores,
    synthesis: scores.synthesis,
    blind_spots: scores.collective_blind_spots,
    siblings: siblingRows.map((r) => ({
      event_id: r.event_id,
      centroid_name: r.centroid_name,
      event_title: r.event_title,
      source_count: r.source_count,
    })),
  });
}

export async function POST(req: NextRequest) {
  try {
    // Auth check (internal key bypass for batch processing)
    const authHeader = req.headers.get('authorization');
    const internalKey = process.env.RAI_INTERNAL_KEY;
    const isInternal = internalKey && authHeader === `Bearer ${internalKey}`;

    if (!isInternal) {
      const session = await auth();
      if (!session?.user) {
        return NextResponse.json({ error: 'Sign in to analyse' }, { status: 401 });
      }
    }

    const { entity_type, entity_id } = await req.json();
    if (!entity_type || !entity_id) {
      return NextResponse.json(
        { error: 'Missing entity_type or entity_id' },
        { status: 400 }
      );
    }

    // Delegate sibling_group to unified handler
    if (entity_type === 'sibling_group') {
      return handleSiblingGroup(entity_id);
    }

    // Check cache
    const cached = await query<{
      sections: string | null;
      scores: unknown;
      synthesis: string | null;
      blind_spots: string[] | null;
      conflicts: string[] | null;
    }>(
      `SELECT sections, scores, synthesis, blind_spots, conflicts
       FROM entity_analyses
       WHERE entity_type = $1 AND entity_id = $2`,
      [entity_type, entity_id]
    );

    if (cached.length > 0 && cached[0].sections) {
      let sections = cached[0].sections;
      if (typeof sections === 'string') {
        try { sections = JSON.parse(sections); } catch { /* use as-is */ }
      }
      return NextResponse.json({
        sections,
        scores: cached[0].scores,
        synthesis: cached[0].synthesis,
        blind_spots: cached[0].blind_spots,
        conflicts: cached[0].conflicts,
      });
    }

    // Fetch stance-clustered narratives for this entity
    const narrativeRows = await query<{
      label: string;
      description: string | null;
      moral_frame: string | null;
      sample_titles: unknown;
      title_count: number;
      cluster_label: string;
      cluster_publishers: string[];
      cluster_score_avg: number;
      signal_stats: SignalStats | null;
    }>(
      `SELECT label, description, moral_frame, sample_titles, title_count,
              cluster_label, cluster_publishers, cluster_score_avg, signal_stats
       FROM narratives
       WHERE entity_type = $1 AND entity_id = $2
         AND extraction_method = 'stance_clustered'
       ORDER BY cluster_score_avg ASC`,
      [entity_type, entity_id]
    );

    if (narrativeRows.length === 0) {
      return NextResponse.json(
        { error: 'No stance-clustered narratives found. Extract narratives first.' },
        { status: 404 }
      );
    }

    // Build cluster narrative inputs
    const clusterNarratives: ClusterNarrative[] = narrativeRows.map((r) => ({
      cluster_label: r.cluster_label || 'unknown',
      cluster_publishers: r.cluster_publishers || [],
      cluster_score_avg: r.cluster_score_avg || 0,
      label: r.label,
      description: r.description,
      moral_frame: r.moral_frame,
      sample_titles: typeof r.sample_titles === 'string'
        ? JSON.parse(r.sample_titles)
        : r.sample_titles || [],
      title_count: r.title_count,
    }));

    // Fetch entity context
    let context: AnalysisContext;
    let stats: SignalStats | null = null;

    let eventDate: string | undefined;

    if (entity_type === 'event') {
      const rows = await query<{
        centroid_id: string;
        centroid_name: string;
        track: string;
        event_title: string;
        event_date: string;
      }>(
        `SELECT c.centroid_id, cv.label as centroid_name, c.track,
                COALESCE(e.title, e.topic_core) as event_title,
                e.date::text as event_date
         FROM events_v3 e
         JOIN ctm c ON c.id = e.ctm_id
         JOIN centroids_v3 cv ON cv.id = c.centroid_id
         WHERE e.id = $1`,
        [entity_id]
      );
      if (rows.length === 0) {
        return NextResponse.json({ error: 'Event not found' }, { status: 404 });
      }
      eventDate = rows[0].event_date;
      context = { ...rows[0], entity_type: 'event' };
    } else {
      const rows = await query<{
        centroid_id: string;
        centroid_name: string;
        track: string;
      }>(
        `SELECT c.centroid_id, cv.label as centroid_name, c.track
         FROM ctm c
         JOIN centroids_v3 cv ON cv.id = c.centroid_id
         WHERE c.id = $1`,
        [entity_id]
      );
      if (rows.length === 0) {
        return NextResponse.json({ error: 'CTM not found' }, { status: 404 });
      }
      context = { ...rows[0], event_title: '', entity_type: 'ctm' };
    }

    // Use signal_stats from first narrative that has them
    for (const r of narrativeRows) {
      if (r.signal_stats) {
        const raw = typeof r.signal_stats === 'string'
          ? JSON.parse(r.signal_stats)
          : r.signal_stats;
        if (raw.title_count || raw.publisher_count) {
          stats = raw;
          break;
        }
      }
    }

    // Select modules deterministically by labels (no LLM call needed)
    // TODO: fetch analytical_labels from event row when available
    const moduleIds = selectModulesByLabels(null);
    const modules = resolveModules(moduleIds);

    // Fetch centroid timeline for temporal context (only events BEFORE this event)
    const eventTags = await query<{ tags: string[] }>(
      `SELECT tags FROM events_v3 WHERE id = $1 AND tags IS NOT NULL`,
      [entity_id]
    ).then((rows) => rows.length > 0 && rows[0].tags ? rows[0].tags : []);

    const timelineEvents = await getCentroidTimeline(
      context.centroid_id,
      [entity_id],
      eventTags,
      90,
      10,
      [],
      eventDate,
    );
    const timelines: CentroidTimeline[] = timelineEvents.length > 0
      ? [{ centroid_name: context.centroid_name, events: timelineEvents }]
      : [];

    // Build prompt, call DeepSeek, parse response
    console.log(`[event-analysis] centroid=${context.centroid_id} eventDate=${eventDate} tags=${eventTags.length} timeline=${timelineEvents.length}`);
    const prompt = buildComparativePrompt(clusterNarratives, context, modules, stats, timelines);
    console.log(`[event-analysis] prompt length: ${prompt.length} chars`);
    const raw = await callDeepSeek(prompt);
    const { sections } = parseAnalysisResponse(raw);
    const scores = parseComparativeScores(raw);

    if (sections.length === 0) {
      console.error('DeepSeek returned no parseable sections for comparative analysis');
      return NextResponse.json({ error: 'Analysis returned no content' }, { status: 502 });
    }

    // Save to entity_analyses
    await query(
      `INSERT INTO entity_analyses
         (entity_type, entity_id, cluster_count, sections, scores,
          synthesis, blind_spots, conflicts)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
       ON CONFLICT (entity_type, entity_id) DO UPDATE SET
         cluster_count = EXCLUDED.cluster_count,
         sections = EXCLUDED.sections,
         scores = EXCLUDED.scores,
         synthesis = EXCLUDED.synthesis,
         blind_spots = EXCLUDED.blind_spots,
         conflicts = EXCLUDED.conflicts,
         created_at = NOW()`,
      [
        entity_type,
        entity_id,
        clusterNarratives.length,
        JSON.stringify(sections),
        JSON.stringify(scores),
        scores.synthesis || null,
        scores.collective_blind_spots?.length ? scores.collective_blind_spots : null,
        null, // conflicts extracted from sections if needed later
      ]
    );

    return NextResponse.json({
      sections,
      scores,
      synthesis: scores.synthesis,
      blind_spots: scores.collective_blind_spots,
    });
  } catch (err: unknown) {
    if (err instanceof Error && err.name === 'AbortError') {
      return NextResponse.json({ error: 'Analysis timed out' }, { status: 504 });
    }
    console.error('Comparative RAI analyse error:', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
