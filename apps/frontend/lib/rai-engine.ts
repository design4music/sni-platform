// ---------------------------------------------------------------------------
// RAI Engine -- local prompt builder, DeepSeek caller, response parser
// Replaces the RAI Render intermediary for WorldBrief narrative analysis.
// ---------------------------------------------------------------------------

import type { SignalStats } from '@/lib/types';

// ---- Types ----------------------------------------------------------------

export interface RaiModule {
  id: string;
  tag: string;
  command: string;
}

export interface NarrativeInput {
  label: string;
  moral_frame: string | null;
  description: string | null;
  sample_titles: Array<{ title: string; publisher: string }>;
  source_count: number;
  top_sources: string[];
}

export interface AnalysisContext {
  centroid_id: string;
  centroid_name: string;
  track: string;
  event_title: string;
  entity_type: string;
}

export interface RaiSection {
  heading: string;
  paragraphs: string[];
}

export interface RaiScores {
  adequacy?: number;
  bias_detected?: number;
  coherence?: number;
  evidence_quality?: number;
  blind_spots?: string[];
  conflicts?: string[];
  synthesis?: string;
}

// ---- Modules (38) -- keyed by ID for lookup after selection ----------------

const MODULE_LIBRARY: Record<string, RaiModule> = {
  'M01': {
    id: 'M01', tag: 'FRAME_CONTEXT',
    command: 'Deconstruct the framing strategy. CHECK: emphasis/omission choices, moral simplification, narrative compression, symbolic/metaphorical shortcuts, conflation of factual and ideological layers.',
  },
  'M02': {
    id: 'M02', tag: 'SYMMETRY_AUDIT',
    command: 'Test evaluative consistency across all actors. CHECK: asymmetric naming (regime vs government, militant vs fighter), toxic labels replacing evidence, emotional register shifts by allegiance, standard-bending for allies.',
  },
  'M03': {
    id: 'M03', tag: 'MATERIAL_GROUND',
    command: 'Establish verified material facts before evaluating framing. CHECK: confirmed actions across independent source chains, scale of harm (deaths, destruction, territorial change), time/place anchoring of claims, where fact ends and interpretation begins.',
  },
  'M04': {
    id: 'M04', tag: 'SOURCE_ECOSYSTEM',
    command: 'Assess whether source diversity reflects epistemic independence or bloc amplification. CHECK: upstream information chains shared across brands, structurally absent perspectives, primary speech omitted or paraphrased away, amplification/suppression asymmetries.',
  },
  'M05': {
    id: 'M05', tag: 'SCALE_SELECTION',
    command: 'Test whether facts are cherry-picked or proportionate. CHECK: strategic selection of facts to steer perception, scale inflation/minimization, baseline manipulation, omission of contextualizing data.',
  },
  'M06': {
    id: 'M06', tag: 'CAUSAL_LOGIC',
    command: 'Evaluate the cause-effect chain for coherence and start-point bias. CHECK: strategic starting-point selection, suppressed earlier causes, narrative contradictions, plausibility of causal leaps, internal consistency.',
  },
  'M07': {
    id: 'M07', tag: 'COMPETING_FRAMES',
    command: 'Surface alternative narratives and identify what is missing. CHECK: competing interpretations from other actors/cultures, facts emphasized vs ignored per frame, strategic narrative gaps, synthesizability of competing versions.',
  },
  'M08': {
    id: 'M08', tag: 'IDENTITY_LEGITIMACY',
    command: 'Detect identity, memory, and institutional legitimacy exploitation. CHECK: weaponized historical trauma, selective collective memory, group identity centering/erasure, international law invoked as rhetorical authority, selective institutional enforcement.',
  },
  'M09': {
    id: 'M09', tag: 'POWER_PURPOSE',
    command: 'Map who benefits and the deeper function of the framing. CHECK: material/symbolic advantage flows, incentive-value misalignment, mobilization vs distraction goals, audience targeting (feel/think/act).',
  },
  'M10': {
    id: 'M10', tag: 'INSTITUTIONAL_CONTROL',
    command: 'Examine how institutions enforce or simulate opposition. CHECK: aligned institutional promotion, dissent punishment mechanisms, performative resistance masking power, control through laws/funding/censure.',
  },
  'M11': {
    id: 'M11', tag: 'FEEDBACK_LOOPS',
    command: 'Identify recursive reinforcement and consensus simulation. CHECK: systematic rebuttal exclusion, loyalty-rewarding feedback channels, dissent pathologization, closed-loop distortion patterns.',
  },
  'M12': {
    id: 'M12', tag: 'STRATEGIC_FORECAST',
    command: 'Project claims forward and track narrative evolution. CHECK: logical consequences if interpretation is true, claim shifts under pressure, abandoned/reinterpreted past claims, risk-context proportionality.',
  },
  'M13': {
    id: 'M13', tag: 'EPISTEMIC_LOAD',
    command: 'Test how knowledge burdens are distributed. CHECK: unstated assumptions treated as common sense, implicit critical elements, asymmetric burden of proof, knowledge gaps papered over.',
  },
  'M14': {
    id: 'M14', tag: 'MORAL_STRATEGIC',
    command: 'Detect moral language masking strategy and narrative stacking. CHECK: virtue signaling serving strategic functions, moral framing exaggerated to obscure realism, layered narratives where surface claims shield deeper agendas.',
  },
  'M15': {
    id: 'M15', tag: 'ACTION_COHERENCE',
    command: 'Compare stated positions with observable actions. CHECK: action-statement gaps, timing contradictions (e.g. strikes during negotiations), resource allocation revealing true priorities, what actions alone reveal.',
  },
  'M16': {
    id: 'M16', tag: 'BLIND_SPOTS_TECH',
    command: 'Reveal systemic blind spots and digital power structures. CHECK: persistently excluded facts/arguments, penalized knowledge, algorithmic governance masking ideology, digital infrastructure dependencies as leverage.',
  },
};

// ---- Module Catalog (compact, for selector prompt) ------------------------

const CORE_MODULE_IDS = ['M01', 'M03', 'M07', 'M16'];
const FALLBACK_ADDITIONAL = ['M06', 'M09', 'M04', 'M02'];

const LABEL_MODULE_MAP: Record<string, string[]> = {
  conflict_military:     ['M06', 'M08', 'M09', 'M15'],
  conflict_diplomatic:   ['M02', 'M06', 'M09', 'M15'],
  power_institutional:   ['M09', 'M10', 'M13', 'M14'],
  economic_leverage:     ['M05', 'M09', 'M12', 'M15'],
  information_control:   ['M02', 'M04', 'M11', 'M13'],
  identity_mobilization: ['M02', 'M08', 'M10', 'M14'],
  sovereignty_violation: ['M06', 'M08', 'M12', 'M15'],
  humanitarian:          ['M02', 'M05', 'M08', 'M14'],
};

/** Select modules by analytical labels. Returns deduplicated list of core + label-mapped modules. */
export function selectModulesByLabels(labels: string[] | null): string[] {
  const ids = new Set(CORE_MODULE_IDS);
  if (labels && labels.length > 0) {
    for (const label of labels) {
      const mapped = LABEL_MODULE_MAP[label];
      if (mapped) {
        for (const id of mapped) ids.add(id);
      }
    }
  } else {
    // No labels available -- use balanced fallback
    for (const id of FALLBACK_ADDITIONAL) ids.add(id);
  }
  return Array.from(ids);
}

// ---- Prompt Builder -------------------------------------------------------

function formatModulesForPrompt(modules: RaiModule[]): string {
  const lines: string[] = ['**ANALYSIS DIMENSIONS:**', ''];
  for (const mod of modules) {
    lines.push(`[${mod.id}] ${mod.tag}: ${mod.command}`);
  }
  lines.push('');
  return lines.join('\n');
}

function formatStatsBlock(stats: SignalStats): string {
  const lines: string[] = ['**COVERAGE STATISTICS:**'];

  lines.push(`- ${stats.publisher_count} publishers, concentration index (HHI): ${stats.publisher_hhi.toFixed(3)} (0=diverse, 1=monopoly)`);

  // Language distribution
  const langEntries = Object.entries(stats.language_distribution)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);
  const total = Object.values(stats.language_distribution).reduce((s, n) => s + n, 0) || 1;
  const langStr = langEntries
    .map(([lang, count]) => `${lang} ${Math.round((count / total) * 100)}%`)
    .join(', ');
  lines.push(`- ${stats.language_count} languages: ${langStr}`);

  // Geographic focus
  const geoEntries = Object.entries(stats.entity_country_distribution || {})
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([cc, count]) => `${cc} (${count})`)
    .join(', ');
  if (geoEntries) lines.push(`- Geographic focus: ${geoEntries}`);

  // Key actors
  const actorStr = (stats.top_actors || []).slice(0, 3).map((a) => a.name).join(', ');
  if (actorStr) lines.push(`- Key actors: ${actorStr}`);

  // Key persons
  const personStr = (stats.top_persons || []).slice(0, 3).map((p) => p.name).join(', ');
  if (personStr) lines.push(`- Key persons: ${personStr}`);

  lines.push(`- Date span: ${stats.date_range_days} days`);

  return lines.join('\n');
}

export function buildAnalysisPrompt(
  narrative: NarrativeInput,
  context: AnalysisContext,
  modules: RaiModule[],
  stats?: SignalStats | null,
): string {
  const parts: string[] = [];

  // 1. System frame
  parts.push(
    'You are operating under the **Real Artificial Intelligence (RAI) Framework**.',
    'This is a **media framing analysis** of news coverage from the WorldBrief intelligence platform.',
    '',
    'Your task:',
    '- Evaluate whether this narrative adequately represents the event',
    '- Identify what perspectives or facts are missing',
    '- Assess source diversity and potential echo-chamber effects',
    '- Detect framing bias and moral simplification',
    '',
  );

  // 2. Context block
  parts.push('**GEOPOLITICAL CONTEXT:**');
  if (context.centroid_name) parts.push(`Region: ${context.centroid_name}`);
  if (context.track) parts.push(`Track: ${context.track}`);
  if (context.event_title) parts.push(`Event: ${context.event_title}`);
  parts.push('');

  // 3. Narrative data
  parts.push('**NARRATIVE FRAME UNDER ANALYSIS:**');
  parts.push(`Label: ${narrative.label}`);
  if (narrative.moral_frame) parts.push(`Moral Frame: ${narrative.moral_frame}`);
  if (narrative.description) parts.push(`Description: ${narrative.description}`);
  parts.push(`Source Count: ${narrative.source_count}`);
  if (narrative.top_sources.length > 0) {
    parts.push(`Top Sources: ${narrative.top_sources.join(', ')}`);
  }
  parts.push('');

  // 4. Coverage statistics (when available)
  if (stats) {
    parts.push(formatStatsBlock(stats));
    parts.push('');
  }

  // 5. Sample headlines
  if (narrative.sample_titles.length > 0) {
    parts.push('**SAMPLE HEADLINES:**');
    const headlines = narrative.sample_titles.slice(0, 15);
    for (const h of headlines) {
      parts.push(`- "${h.title}" (${h.publisher})`);
    }
    parts.push('');
  }

  // 6. Module descriptions with premises
  parts.push(formatModulesForPrompt(modules));

  // 7. Output format instructions
  parts.push(
    '**OUTPUT FORMAT INSTRUCTIONS:**',
    '- Use `## ` (h2) for each dimension heading using the tag name (e.g., ## Frame & Context Assessment, ## Symmetry Audit)',
    '- Do NOT include module IDs (M01, M02...) in headings -- use descriptive titles only',
    '- Use bullet lists for findings and blind spots',
    '- Keep each section to 2-4 paragraphs max',
    '- Mark key insights with `> ` blockquote syntax',
    '- Use `### ` (h3) for sub-sections if needed',
    '',
  );

  // 9. Scoring instruction
  parts.push(
    '**At the end of your analysis**, output a scoring block in this exact format:',
    '',
    'SCORES: {"adequacy": <0.0-1.0>, "bias_detected": <0.0-1.0>, "coherence": <0.0-1.0>, "evidence_quality": <0.0-1.0>, "blind_spots": ["...", "..."], "conflicts": ["...", "..."], "synthesis": "<1-2 sentence summary>"}',
    '',
    'The scores must reflect your actual analysis. Do NOT use placeholder values.',
  );

  return parts.join('\n');
}

// ---- User Input Prompt (freeform text analysis) ----------------------------

export function buildUserInputPrompt(
  userText: string,
  modules: RaiModule[],
): string {
  const parts: string[] = [];

  parts.push(
    'You are operating under the **Real Artificial Intelligence (RAI) Framework**.',
    'A user has submitted a text for critical analysis. This could be a news narrative, a political claim, a media excerpt, or any geopolitical statement.',
    '',
    'Your task:',
    '- Deconstruct the framing, assumptions, and implicit claims in the text',
    '- Identify what perspectives, facts, or actors are missing or underrepresented',
    '- Assess logical coherence, evidence quality, and potential bias',
    '- Highlight blind spots and suggest what a fuller picture would include',
    '',
  );

  parts.push('**USER-SUBMITTED TEXT:**');
  parts.push('```');
  parts.push(userText);
  parts.push('```');
  parts.push('');

  // Module descriptions
  parts.push(formatModulesForPrompt(modules));

  parts.push(
    '**OUTPUT FORMAT INSTRUCTIONS:**',
    '- Use `## ` (h2) for each dimension heading using descriptive titles',
    '- Do NOT include module IDs (M01, M02...) in headings',
    '- Use bullet lists for findings and blind spots',
    '- Keep each section to 2-4 paragraphs max',
    '- Mark key insights with `> ` blockquote syntax',
    '',
  );

  parts.push(
    '**At the end of your analysis**, output a scoring block in this exact format:',
    '',
    'SCORES: {"frame_divergence": <0.0-1.0>, "collective_blind_spots": ["...", "..."], "synthesis": "<1-2 sentence summary>"}',
    '',
    'The scores must reflect your actual analysis. Do NOT use placeholder values.',
  );

  return parts.join('\n');
}

// ---- DeepSeek Caller ------------------------------------------------------

const DEEPSEEK_API_URL =
  process.env.DEEPSEEK_API_URL || 'https://api.deepseek.com/v1/chat/completions';
const DEEPSEEK_MODEL = process.env.DEEPSEEK_MODEL || 'deepseek-chat';
const DEEPSEEK_API_KEY = process.env.DEEPSEEK_API_KEY || '';
const DEEPSEEK_TIMEOUT_MS = 150_000;

export async function callDeepSeek(prompt: string, maxTokens: number = 4000): Promise<string> {
  if (!DEEPSEEK_API_KEY) {
    throw new Error('DEEPSEEK_API_KEY not configured');
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), DEEPSEEK_TIMEOUT_MS);

  try {
    const res = await fetch(DEEPSEEK_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${DEEPSEEK_API_KEY}`,
      },
      body: JSON.stringify({
        model: DEEPSEEK_MODEL,
        messages: [{ role: 'user', content: prompt }],
        temperature: 0.3,
        max_tokens: maxTokens,
      }),
      signal: controller.signal,
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`DeepSeek API error ${res.status}: ${text.slice(0, 300)}`);
    }

    const data = await res.json();
    const content = data.choices?.[0]?.message?.content;
    if (!content) {
      throw new Error('DeepSeek returned empty response');
    }
    return content;
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new Error('DeepSeek request timed out');
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}

// ---- Response Parser ------------------------------------------------------

function parseScores(raw: string): RaiScores {
  // Stage 1: SCORES: prefix
  let m = raw.match(/SCORES:\s*(\{[\s\S]*?\})/);
  if (m) {
    try {
      return JSON.parse(m[1]);
    } catch { /* fall through */ }
  }

  // Stage 2: code-fenced JSON with "adequacy"
  m = raw.match(/```(?:json)?\s*(\{[^`]*"adequacy"[^`]*\})\s*```/);
  if (m) {
    try {
      return JSON.parse(m[1]);
    } catch { /* fall through */ }
  }

  // Stage 3: any JSON block with "adequacy"
  const blocks = raw.matchAll(/\{[^{}]{10,}\}/g);
  for (const block of blocks) {
    try {
      const obj = JSON.parse(block[0]);
      if ('adequacy' in obj) return obj;
    } catch { /* continue */ }
  }

  return {};
}

export function parseAnalysisResponse(raw: string): {
  sections: RaiSection[];
  scores: RaiScores;
} {
  const scores = parseScores(raw);

  // Strip the SCORES block from prose
  let prose = raw
    .replace(/SCORES:\s*\{[\s\S]*?\}\s*/g, '')
    .replace(/```(?:json)?\s*\{[^`]*"adequacy"[^`]*\}\s*```/g, '')
    .trim();

  // Split on ## or ### headings
  const sections: RaiSection[] = [];
  const headingPattern = /^(#{2,3})\s+(.+)$/gm;
  const headings: Array<{ level: number; title: string; index: number }> = [];

  let match;
  while ((match = headingPattern.exec(prose)) !== null) {
    headings.push({
      level: match[1].length,
      title: match[2].trim(),
      index: match.index,
    });
  }

  if (headings.length === 0) {
    // No headings found -- return entire response as single section
    sections.push({
      heading: 'Analysis',
      paragraphs: splitParagraphs(prose),
    });
  } else {
    // Optional text before first heading
    const before = prose.slice(0, headings[0].index).trim();
    if (before) {
      sections.push({
        heading: 'Overview',
        paragraphs: splitParagraphs(before),
      });
    }

    for (let i = 0; i < headings.length; i++) {
      const start = headings[i].index + (prose.slice(headings[i].index).indexOf('\n') + 1 || prose.length);
      const end = i + 1 < headings.length ? headings[i + 1].index : prose.length;
      const body = prose.slice(start, end).trim();

      sections.push({
        heading: headings[i].title,
        paragraphs: splitParagraphs(body),
      });
    }
  }

  return { sections, scores };
}

function splitParagraphs(text: string): string[] {
  if (!text) return [];
  // Split on double newlines, keep single newlines within paragraphs
  return text
    .split(/\n{2,}/)
    .map((p) => p.trim())
    .filter((p) => p.length > 0);
}

// ---- Helpers for route.ts -------------------------------------------------

/** Resolve module IDs to RaiModule objects. Skips unknown IDs. */
export function resolveModules(ids: string[]): RaiModule[] {
  const modules: RaiModule[] = [];
  for (const id of ids) {
    const mod = MODULE_LIBRARY[id];
    if (mod) modules.push(mod);
  }
  return modules;
}

/** Core module IDs that are always included in analysis. */
export { CORE_MODULE_IDS, LABEL_MODULE_MAP };


// ---- Comparative Analysis (multi-narrative) --------------------------------

export interface ClusterNarrative {
  cluster_label: string;       // critical | reportorial | supportive
  cluster_publishers: string[];
  cluster_score_avg: number;
  label: string;               // narrative frame label
  description: string | null;
  moral_frame: string | null;
  sample_titles: Array<{ title: string; publisher: string }>;
  title_count: number;
  centroid_name?: string;      // for cross-centroid unified analysis
}

export interface CentroidTimeline {
  centroid_name: string;
  events: Array<{
    title: string;
    date: string;
    importance_score: number | null;
    source_count: number;
  }>;
}

function formatTimelineBlock(timelines: CentroidTimeline[]): string {
  if (timelines.length === 0) return '';
  const parts: string[] = [];
  parts.push('**PRIOR EVENTS (90-day timeline):**');
  parts.push('Reference specific prior events when they explain current framing choices.');
  parts.push('');
  for (const tl of timelines) {
    parts.push(`${tl.centroid_name}:`);
    const sorted = [...tl.events].sort((a, b) => a.date.localeCompare(b.date));
    for (const ev of sorted) {
      parts.push(`- ${ev.date}: ${ev.title} (${ev.source_count} sources)`);
    }
    parts.push('');
  }
  return parts.join('\n');
}

export interface ComparativeScores {
  frame_divergence: number;
  collective_blind_spots: string[];
  synthesis: string;
}

export function buildComparativePrompt(
  narratives: ClusterNarrative[],
  context: AnalysisContext,
  modules: RaiModule[],
  stats?: SignalStats | null,
  timelines?: CentroidTimeline[],
): string {
  const parts: string[] = [];

  // 1. System frame
  parts.push(
    'You are a strategic analyst. Produce a comparative media framing analysis of ' + narratives.length + ' editorial stance groups covering the same event.',
    '',
    'Write ONE integrated brief. For each analysis dimension:',
    '- Where editorial groups CONVERGE (shared assumptions) and DIVERGE (contested elements)',
    '- What each group OMITS that another includes',
    '- What ALL groups omit (collective blind spots)',
    '',
    '**ACTOR MAPPING:** Surface ALL actors with significant impact -- direct parties, indirect influencers, background beneficiaries. Actors invisible in coverage are often most important. Flag actors who: (a) lobby for/against resolution, (b) act contrary to stated goals, (c) shape policy through institutional influence.',
    '',
  );

  // 2. Context
  parts.push('**GEOPOLITICAL CONTEXT:**');
  if (context.centroid_name) parts.push(`Region: ${context.centroid_name}`);
  if (context.track) parts.push(`Track: ${context.track}`);
  if (context.event_title) parts.push(`Event: ${context.event_title}`);
  parts.push('');

  // 2b. Centroid timeline (temporal context)
  if (timelines && timelines.length > 0) {
    parts.push(formatTimelineBlock(timelines));
  }

  // 3. Editorial stance groups
  parts.push('**EDITORIAL STANCE GROUPS:**');
  parts.push('');
  for (const n of narratives) {
    const pubList = n.cluster_publishers.slice(0, 5).join(', ');
    const extra = n.cluster_publishers.length > 5
      ? ` +${n.cluster_publishers.length - 5}` : '';
    parts.push(`**${n.cluster_label.toUpperCase()}** (stance ${n.cluster_score_avg.toFixed(1)}, ${n.title_count} titles, ${n.cluster_publishers.length} publishers: ${pubList}${extra})`);
    parts.push(`Frame: "${n.label}"`);
    if (n.description) parts.push(`Position: ${n.description}`);
    if (n.moral_frame) parts.push(`Moral frame: ${n.moral_frame}`);

    if (n.sample_titles.length > 0) {
      for (const h of n.sample_titles.slice(0, 5)) {
        parts.push(`- "${h.title}" (${h.publisher})`);
      }
    }
    parts.push('');
  }

  // 4. Coverage statistics
  if (stats) {
    parts.push(formatStatsBlock(stats));
    parts.push('');
  }

  // 5. Module descriptions with premises
  parts.push(formatModulesForPrompt(modules));

  // 6. Output format + metrics
  parts.push(
    '**OUTPUT FORMAT:**',
    'Use `## ` (h2) per analysis dimension with descriptive titles (e.g. ## Frame & Context Assessment, ## Symmetry Audit).',
    'Do NOT include module IDs (M01, M02...) in headings.',
    'Each section: comparative, 2-3 paragraphs. Use `> ` for key insights.',
    'Use plain language throughout -- no internal codes, framework IDs, or technical jargon.',
    'Refer to editorial groups by their stance label (e.g. "the critical group", "the reportorial group"), not as "clusters" or "centroids".',
    '',
    'After analysis dimensions, add:',
    '`## Actors Beyond the Frame` -- actors with significant but underrepresented influence. For each: structural interest, actions, why coverage minimizes them.',
    '`## Convergence & Collective Blind Spots` -- shared assumptions and gaps across ALL editorial groups.',
    '`## Further Investigation` -- 2-3 historical periods to study, 2-3 books (only cite well-known works), 3-4 research questions, key economic/structural factors invisible in coverage.',
    '',
    'End with: SCORES: {"frame_divergence": <0-1>, "collective_blind_spots": ["..."], "synthesis": "<1-2 sentence assessment>"}',
  );

  return parts.join('\n');
}

/**
 * Build a unified comparative prompt for cross-centroid sibling events.
 * Groups narratives by centroid and adds a "Coverage Lens Shift" section.
 */
export function buildUnifiedComparativePrompt(
  narrativesByCentroid: Map<string, ClusterNarrative[]>,
  siblingEvents: Array<{ centroid_name: string; event_title: string; source_count: number }>,
  modules: RaiModule[],
  stats?: SignalStats | null,
  timelines?: CentroidTimeline[],
): string {
  const parts: string[] = [];

  // 1. System frame
  parts.push(
    'You are a strategic analyst. Produce a cross-country comparative analysis: the SAME event appears under DIFFERENT country coverage ecosystems, each with its own publisher composition.',
    'Publisher migration between editorial stance groups across countries IS the core signal.',
    '',
    'Write ONE integrated brief. For each analysis dimension:',
    '- How framing shifts across country lenses',
    '- Publishers that change editorial stance across countries and why',
    '- Where groups CONVERGE, DIVERGE, and what each country\'s coverage OMITS',
    '',
    '**ACTOR MAPPING:** Surface ALL actors with significant impact -- direct, indirect, invisible. Flag actors who: (a) lobby for/against resolution, (b) act contrary to stated goals, (c) shape policy through institutional influence.',
    '',
  );

  // 2. Cross-country events context
  parts.push('**CROSS-COUNTRY COVERAGE:**');
  for (const ev of siblingEvents) {
    parts.push(`- **${ev.centroid_name}**: "${ev.event_title}" (${ev.source_count} sources)`);
  }
  parts.push('');

  // 2b. Country timelines (temporal context)
  if (timelines && timelines.length > 0) {
    parts.push(formatTimelineBlock(timelines));
  }

  // 3. Editorial stance groups by country
  parts.push('**EDITORIAL STANCE GROUPS BY COUNTRY:**');
  parts.push('');
  for (const [centroidName, narratives] of narrativesByCentroid) {
    parts.push(`### ${centroidName.toUpperCase()}`);
    for (const n of narratives) {
      const pubList = n.cluster_publishers.slice(0, 5).join(', ');
      const extra = n.cluster_publishers.length > 5
        ? ` +${n.cluster_publishers.length - 5}` : '';
      parts.push(`**${n.cluster_label.toUpperCase()}** (stance ${n.cluster_score_avg.toFixed(1)}, ${n.title_count} titles, ${n.cluster_publishers.length} publishers: ${pubList}${extra})`);
      parts.push(`Frame: "${n.label}"`);
      if (n.description) parts.push(`Position: ${n.description}`);
      if (n.moral_frame) parts.push(`Moral frame: ${n.moral_frame}`);

      if (n.sample_titles.length > 0) {
        for (const h of n.sample_titles.slice(0, 3)) {
          parts.push(`- "${h.title}" (${h.publisher})`);
        }
      }
      parts.push('');
    }
  }

  // 4. Analysis dimensions
  parts.push(formatModulesForPrompt(modules));

  // 5. Output format + metrics
  parts.push(
    '**OUTPUT FORMAT:**',
    'Use `## ` (h2) per analysis dimension with descriptive titles (e.g. ## Frame & Context Assessment, ## Symmetry Audit).',
    'Do NOT include module IDs (M01, M02...) in headings.',
    'Each section: comparative across countries, 2-3 paragraphs. Use `> ` for key insights.',
    'Use plain language throughout -- no internal codes, framework IDs, or technical jargon.',
    'Refer to editorial groups by their stance label (e.g. "the critical group", "the supportive group"), not as "clusters".',
    'Refer to country coverage by country name, not as "centroids".',
    '',
    'After analysis dimensions, add:',
    '`## Coverage Lens Shift` -- CORE SECTION. How publishers shift editorial stance across countries, frames that appear/disappear per country lens.',
    '`## Actors Beyond the Frame` -- Actors with significant but underrepresented influence.',
    '`## Convergence & Collective Blind Spots` -- Shared assumptions and gaps across ALL countries.',
    '`## Further Investigation` -- 2-3 historical periods, 2-3 books (well-known only), 3-4 research questions, key economic/structural factors.',
    '',
    'End with: SCORES: {"frame_divergence": <0-1>, "collective_blind_spots": ["..."], "synthesis": "<1-2 sentence assessment>"}',
  );

  return parts.join('\n');
}

export function parseComparativeScores(raw: string): ComparativeScores {
  const defaults: ComparativeScores = {
    frame_divergence: 0.5,
    collective_blind_spots: [],
    synthesis: '',
  };

  let m = raw.match(/SCORES:\s*(\{[\s\S]*?\})\s*$/m);
  if (!m) {
    m = raw.match(/```(?:json)?\s*(\{[^`]*"cluster_scores"[^`]*\})\s*```/);
  }
  if (!m) return defaults;

  try {
    const parsed = JSON.parse(m[1]);
    return {
      frame_divergence: parsed.frame_divergence ?? 0.5,
      collective_blind_spots: parsed.collective_blind_spots || [],
      synthesis: parsed.synthesis || '',
    };
  } catch {
    return defaults;
  }
}
