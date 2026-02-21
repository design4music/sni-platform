// ---------------------------------------------------------------------------
// RAI Engine -- local prompt builder, DeepSeek caller, response parser
// Replaces the RAI Render intermediary for WorldBrief narrative analysis.
// ---------------------------------------------------------------------------

// ---- Types ----------------------------------------------------------------

export interface RaiModule {
  id: string;
  name: string;
  purpose: string;
  core_questions: string[];
  wisdom_injected: string[];
  philosophical_anchoring: string[]; // premise IDs
}

export interface RaiPremise {
  title: string;
  content: string;
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

// ---- Premises (14) -------------------------------------------------------

const PREMISE_LIBRARY: Record<string, RaiPremise> = {
  'D1.1': {
    title: 'Power is rarely surrendered; it is redistributed through ritual, consensus, or coercion',
    content: 'In all functioning systems -- democratic, autocratic, or hybrid -- true power shifts occur under one of three conditions: Elite consensus to preserve stability, External pressure or control, or Systemic fracture or collapse. Elections and constitutional processes are often choreographed simulations to legitimize decisions already negotiated behind closed doors.',
  },
  'D2.3': {
    title: 'Neutrality becomes illusion in systemic conflict',
    content: 'In high-stakes global competition, all states are drawn into alignment, either through dependence, coercion, or survival instinct. True neutrality is impossible in a deeply interconnected world.',
  },
  'D3.2': {
    title: 'Censorship and visibility are asymmetric tools',
    content: 'Control over digital infrastructure -- platforms, algorithms, recommendation engines, content policies -- enables nonlinear narrative dominance. What is suppressed is often less important than what is invisibly sidelined.',
  },
  'D3.3': {
    title: 'Perception is power',
    content: 'Legitimacy, victimhood, and moral high ground are not just narratives -- they are operational assets. Winning the story often has greater strategic value than winning the terrain. Modern information warfare includes memetic injection, coordinated emotional framing, information flooding, and virality engineering.',
  },
  'D4.1': {
    title: 'Cultural self-image distorts memory',
    content: 'Societies tend to idealize their past, suppressing atrocities, defeats, or failures. Collective memory is selectively curated through trauma editing, symbolic purification, and ritualized storytelling in education, monuments, and national holidays.',
  },
  'D4.3': {
    title: 'Civilizations pursue different visions of success',
    content: 'All cultures strive for stability, continuity, and influence -- but their definitions of success vary profoundly. Some prioritize expansion or technological progress; others value harmony, survival, or spiritual legacy. Judging them by a single universal standard often reflects ideological projection, not objective analysis.',
  },
  'D5.1': {
    title: 'Systems behave through feedback, not intention',
    content: 'Outcomes in complex systems are not directly caused by intentions but emerge from interactions between variables, delays, and feedback loops. Even rational actors are swept into patterns beyond their awareness or control. Linear explanations almost always miss the real cause.',
  },
  'D5.2': {
    title: 'Fragile systems suppress dissent',
    content: 'When systems lack flexibility or redundancy, they tighten control in response to perceived threats. Repression is not always ideological -- it is often a survival reflex in systems approaching failure.',
  },
  'D5.3': {
    title: 'Stability depends on controlled transparency',
    content: 'No system can operate in full opacity -- or in full daylight. Long-term resilience often requires a managed flow of visibility: enough to maintain legitimacy, but not so much that its contradictions become uncontrollable.',
  },
  'D6.1': {
    title: 'Multiple value systems can be valid within their own logic',
    content: 'Different ethical traditions -- religious, cultural, strategic -- can produce conflicting judgments without either being objectively false. What is "just" in one worldview may be "barbaric" in another. Ethical analysis requires context, not universalization.',
  },
  'D6.2': {
    title: 'Moral certainty often masks geopolitical or institutional interests',
    content: 'The language of "values" and "human rights" is frequently used to cloak strategic motives. Claiming virtue becomes a tool of leverage, especially when paired with sanctions, military action, or selective outrage.',
  },
  'D6.6': {
    title: 'Hypocrisy is not an anomaly, but a structural feature of moral discourse',
    content: 'Nations, institutions, and individuals often fail to meet the standards they preach -- not merely from weakness, but because moral language is strategically deployed to manage perception, not guide consistent behavior.',
  },
  'D7.2': {
    title: 'Delayed outcomes are often more impactful than immediate ones',
    content: 'What seems like success in the short term may erode legitimacy or stability over time. Systems have latency, and interventions often unleash feedback loops that manifest far later. Strategic judgment demands temporal patience.',
  },
  'D8.4': {
    title: 'Debt is a tool of control, not just finance',
    content: 'Public and private debt create long-term dependency structures. Lenders can shape policy, impose austerity, and dictate reforms under the guise of fiscal discipline or development assistance.',
  },
};

// ---- Modules (6) ----------------------------------------------------------

const MODULE_LIBRARY: RaiModule[] = [
  {
    id: 'CL-0',
    name: 'Narrative Contextualization and Framing Assessment',
    purpose: 'Contextualize the narrative frame within the broader event and assess its framing strategy. Evaluate what framing choices were made, what moral simplification reveals about the source ecosystem, and how the narrative positions itself relative to the full scope of the event.',
    core_questions: [
      'How does this narrative frame position itself relative to the broader event?',
      'What framing choices (emphasis, omission, moral anchoring) shape this narrative?',
      'What does the moral simplification reveal about the source ecosystem producing it?',
      'Are there factual, narrative, or systemic components being conflated or separated?',
    ],
    wisdom_injected: [
      'Every frame is a choice -- and every choice reveals an agenda.',
      'Moral simplification is not clarity; it is strategy.',
      'Honor the complexity. Clean the lens.',
    ],
    philosophical_anchoring: ['D1.1', 'D6.2'],
  },
  {
    id: 'NL-1',
    name: 'Cause-Effect Chain Analysis',
    purpose: 'Evaluate whether cause-and-effect logic is coherent, plausible, and properly sequenced -- with careful attention to where the chain begins.',
    core_questions: [
      'Are causes and consequences logically connected?',
      'Is the sequence clear, or manipulated to create confusion or moral reversal?',
      'Are plausible alternative causes or interpretations acknowledged?',
      'Start-Point Bias Check: Is the chosen starting point contested or strategically selected? Are earlier causes being ignored?',
    ],
    wisdom_injected: [
      'Causality is not a straight line -- it is a choice of lens.',
      'Every chain has a beginning -- but not every beginning is the truth.',
      'The origin you choose is the side you have chosen.',
    ],
    philosophical_anchoring: ['D4.1', 'D4.3', 'D7.2'],
  },
  {
    id: 'NL-3',
    name: 'Competing Narratives Contrast',
    purpose: 'Surface alternative narratives to evaluate blind spots, cultural framings, or missing dimensions.',
    core_questions: [
      'What other groups or actors interpret this differently?',
      'What facts do those narratives emphasize or ignore?',
      'Are they mutually exclusive or potentially synthesizable?',
      'Who benefits from each version?',
    ],
    wisdom_injected: [
      'The truth may be divided, but the lies are often complete.',
      'Multiple lenses sharpen the image.',
    ],
    philosophical_anchoring: ['D3.3', 'D6.1', 'D8.4'],
  },
  {
    id: 'FL-2',
    name: 'Asymmetrical Amplification Awareness',
    purpose: 'Detect whether claims are being unnaturally promoted or suppressed due to information control asymmetries.',
    core_questions: [
      'Is the claim widely echoed across high-power media or ignored despite relevance?',
      'Are opposing versions of the claim visible and credible?',
      'Who has the megaphone? Who has been silenced?',
      'What explains the amplification pattern?',
    ],
    wisdom_injected: [
      'What is repeated is not necessarily true.',
      'Silence is often manufactured.',
      'Volume reveals agenda.',
    ],
    philosophical_anchoring: ['D3.2', 'D5.1', 'D6.6'],
  },
  {
    id: 'FL-3',
    name: 'Source Independence Audit',
    purpose: 'Evaluate the independence, diversity, and reliability of sources cited or implied. Spot coordinated narratives or echo chambers.',
    core_questions: [
      'Are the cited sources directly involved, third-party, or anonymous?',
      'Is there over-reliance on aligned actors?',
      'Do citations originate from power-linked networks (gov, media groups, NGOs)?',
      'What does the source ecosystem reveal about the claim?',
    ],
    wisdom_injected: [
      'Power speaks in chorus.',
      'Independence is not a brand, it is a structure.',
      'Follow the source chain to find the source.',
    ],
    philosophical_anchoring: ['D2.3', 'D5.2', 'D3.2'],
  },
  {
    id: 'SL-8',
    name: 'Systemic Blind Spots and Vulnerabilities',
    purpose: 'Reveal what the system or dominant information flow cannot process -- its blind spots, silences, or forbidden truths.',
    core_questions: [
      'What facts or arguments are persistently excluded?',
      'What questions cannot be asked in polite society?',
      'What knowledge is penalized?',
    ],
    wisdom_injected: [
      'Systems fear what they cannot metabolize.',
      'The unspeakable reveals the ungovernable.',
    ],
    philosophical_anchoring: ['D3.2', 'D5.3', 'D8.4'],
  },
];

// ---- Prompt Builder -------------------------------------------------------

function formatModulesForPrompt(): string {
  const moduleIds = MODULE_LIBRARY.map((m) => m.id);
  const lines: string[] = [
    '**SELECTED RAI ANALYSIS COMPONENTS:**',
    '',
    `**Execution Order:** ${moduleIds.join(' -> ')}`,
    '',
  ];

  for (const mod of MODULE_LIBRARY) {
    lines.push(`**${mod.id}: ${mod.name}**`);
    lines.push(`*Purpose:* ${mod.purpose}`);
    lines.push('');
    lines.push('*Core Questions:*');
    for (const q of mod.core_questions) {
      lines.push(`- ${q}`);
    }
    lines.push('');
    lines.push('*Philosophical Anchoring:*');
    for (const pid of mod.philosophical_anchoring) {
      const premise = PREMISE_LIBRARY[pid];
      if (premise) {
        lines.push(`- **${pid}**: ${premise.title}`);
        lines.push(`  ${premise.content}`);
      }
    }
    lines.push('');
    lines.push('*Wisdom Guidance:*');
    for (const w of mod.wisdom_injected) {
      lines.push(`- *${w}*`);
    }
    lines.push('');
    lines.push('---');
    lines.push('');
  }

  return lines.join('\n');
}

export function buildAnalysisPrompt(
  narrative: NarrativeInput,
  context: AnalysisContext,
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

  // 4. Sample headlines
  if (narrative.sample_titles.length > 0) {
    parts.push('**SAMPLE HEADLINES:**');
    const headlines = narrative.sample_titles.slice(0, 15);
    for (const h of headlines) {
      parts.push(`- "${h.title}" (${h.publisher})`);
    }
    parts.push('');
  }

  // 5. Module descriptions with premises
  parts.push(formatModulesForPrompt());

  // 6. Output format instructions
  parts.push(
    '**OUTPUT FORMAT INSTRUCTIONS:**',
    '- Use `## ` (h2) for each module heading (e.g., ## CL-0: Narrative Contextualization)',
    '- Use bullet lists for findings and blind spots',
    '- Keep each section to 2-4 paragraphs max',
    '- Mark philosophical insights with `> ` blockquote syntax',
    '- Use `### ` (h3) for sub-sections within a module if needed',
    '',
  );

  // 7. Premise citation instruction
  parts.push(
    'When referencing RAI premises (D1.1, D2.5, etc.), always explain what the premise says inline rather than just citing the ID. The reader does not have access to the premise library.',
    '',
  );

  // 8. Scoring instruction
  parts.push(
    '**At the end of your analysis**, output a scoring block in this exact format:',
    '',
    'SCORES: {"adequacy": <0.0-1.0>, "bias_detected": <0.0-1.0>, "coherence": <0.0-1.0>, "evidence_quality": <0.0-1.0>, "blind_spots": ["...", "..."], "conflicts": ["...", "..."], "synthesis": "<1-2 sentence summary>"}',
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
const DEEPSEEK_TIMEOUT_MS = 120_000;

export async function callDeepSeek(prompt: string): Promise<string> {
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
        max_tokens: 4000,
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
