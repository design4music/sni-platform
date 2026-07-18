// Test script for new RAI Material Impact Grounding (CL-6) + Coverage Ecosystem Diagnosis (CL-7)
// Usage: cd apps/frontend && npx tsx ../../scripts/test_rai_grounding.ts
// Reads DEEPSEEK_API_KEY from apps/frontend/.env.local

import * as fs from 'fs';
import * as path from 'path';

// ---- Load env from .env.local ----
const envPath = path.resolve(__dirname, '../apps/frontend/.env.local');
const envContent = fs.readFileSync(envPath, 'utf-8');
for (const line of envContent.split('\n')) {
  const clean = line.replace(/\r$/, '');
  const m = clean.match(/^([A-Z_]+)=(.+)$/);
  if (m) process.env[m[1]] = m[2].trim();
}

const API_KEY = process.env.DEEPSEEK_API_KEY!;
const API_URL = process.env.DEEPSEEK_API_URL || 'https://api.deepseek.com/v1/chat/completions';
const MODEL = process.env.DEEPSEEK_MODEL || 'deepseek-chat';

// ---- Minimal type defs ----
interface TestCase {
  name: string;
  narrative_label: string;
  moral_frame: string;
  description: string;
  event_title: string;
  centroid_name: string;
  track: string;
  sample_titles: Array<{ title: string; publisher: string }>;
  source_count: number;
  top_sources: string[];
  publisher_count: number;
  publisher_hhi: number;
  language_count: number;
  language_distribution: Record<string, number>;
}

// ---- Three test cases ----
const CASES: TestCase[] = [
  {
    name: 'Iran - US/Israel Attack',
    narrative_label: 'Iran as Victim of Aggression',
    moral_frame: 'Hero: Iran (victim), Villain: Israel/US (aggressors/assassins)',
    description: 'Frames the killing of Khamenei as an unjustified assassination and act of war, legitimizing Iran\'s right to retaliate.',
    event_title: 'US-Israeli strikes on Tehran kill Supreme Leader Khamenei',
    centroid_name: 'Iran',
    track: 'Geopolitics',
    sample_titles: [
      { title: 'Iran vows revenge after Israeli strikes kill Supreme Leader Khamenei', publisher: 'Al Jazeera' },
      { title: 'Tehran in flames: US-backed strikes target Iranian capital', publisher: 'CGTN' },
      { title: 'IRGC declares war footing after assassination of Khamenei', publisher: 'Press TV' },
      { title: 'World leaders condemn strikes on Tehran as act of war', publisher: 'TASS' },
      { title: 'Iran mourns Khamenei as millions take to streets', publisher: 'Dawn' },
      { title: 'Pentagon confirms US role in strikes targeting Iranian leadership', publisher: 'Reuters' },
      { title: 'Israel claims preemptive strike neutralized nuclear threat', publisher: 'Times of Israel' },
      { title: 'Iran retaliates with missile barrage on Israeli military bases', publisher: 'BBC' },
      { title: 'UN Security Council emergency session on Iran crisis', publisher: 'France 24' },
      { title: 'Oil prices surge 30% as Middle East conflict escalates', publisher: 'Bloomberg' },
    ],
    source_count: 340,
    top_sources: ['Al Jazeera', 'BBC', 'Reuters', 'CGTN', 'Press TV', 'France 24', 'TASS'],
    publisher_count: 85,
    publisher_hhi: 0.04,
    language_count: 12,
    language_distribution: { en: 180, ar: 55, fa: 30, fr: 25, de: 15, es: 12, ru: 10, zh: 8, tr: 5 },
  },
  {
    name: 'Russia/Ukraine - Civilian Suffering',
    narrative_label: 'Russian Aggression Against Ukrainian Civilians',
    moral_frame: 'Hero: Ukraine (democratic victim), Villain: Russia (imperial aggressor)',
    description: 'Frames Russia as deliberately targeting Ukrainian civilians in an unprovoked invasion, emphasizing war crimes and Western solidarity with Ukraine.',
    event_title: 'Russian strikes on Ukrainian infrastructure kill dozens',
    centroid_name: 'Ukraine',
    track: 'Geopolitics',
    sample_titles: [
      { title: 'Russia launches massive missile barrage on Ukrainian cities, killing 47', publisher: 'CNN' },
      { title: 'Zelensky pleads for more air defense after deadly Russian strikes', publisher: 'BBC' },
      { title: 'War crimes evidence mounts as Russia targets civilian infrastructure', publisher: 'The Guardian' },
      { title: 'NATO allies pledge additional air defense systems to Ukraine', publisher: 'Reuters' },
      { title: 'Hospitals overwhelmed after Russian strikes on Kharkiv', publisher: 'Washington Post' },
      { title: 'EU condemns barbaric Russian attacks on civilian targets', publisher: 'DW' },
      { title: 'Survivors describe horror of Russian missile attack on residential area', publisher: 'NYT' },
      { title: 'Ukraine needs more weapons to stop Russian terror, says defense minister', publisher: 'Politico' },
      { title: 'Red Cross reports critical humanitarian situation in eastern Ukraine', publisher: 'AFP' },
      { title: 'Russian offensive stalls but bombardment of cities intensifies', publisher: 'The Times' },
    ],
    source_count: 520,
    top_sources: ['CNN', 'BBC', 'Reuters', 'The Guardian', 'NYT', 'Washington Post', 'AFP'],
    publisher_count: 145,
    publisher_hhi: 0.02,
    language_count: 15,
    language_distribution: { en: 280, de: 45, fr: 40, pl: 30, es: 25, uk: 20, it: 18, nl: 12, sv: 10, pt: 10, ja: 8, ko: 7, cs: 5, ro: 5, ru: 5 },
  },
  {
    name: 'Israel/Palestine - Gaza Conflict',
    narrative_label: 'Israeli Military Operation as Self-Defense',
    moral_frame: 'Hero: Israel (defending citizens), Villain: Hamas (terrorists)',
    description: 'Frames Israeli military operations in Gaza as legitimate self-defense against Hamas terrorism, emphasizing October 7 and hostage crisis.',
    event_title: 'Israeli operations in Gaza continue amid rising civilian toll',
    centroid_name: 'Israel-Palestine',
    track: 'Geopolitics',
    sample_titles: [
      { title: 'IDF continues operations to dismantle Hamas infrastructure in Gaza', publisher: 'Times of Israel' },
      { title: 'Gaza death toll passes 40,000 as Israeli offensive continues', publisher: 'Al Jazeera' },
      { title: 'Israel says it has eliminated senior Hamas commanders in latest strikes', publisher: 'Reuters' },
      { title: 'Humanitarian crisis deepens in Gaza as aid deliveries blocked', publisher: 'BBC' },
      { title: 'US reaffirms Israel\'s right to self-defense against Hamas', publisher: 'CNN' },
      { title: 'UN reports widespread destruction of civilian infrastructure in Gaza', publisher: 'AFP' },
      { title: 'Families of hostages demand government prioritize deal over military ops', publisher: 'Haaretz' },
      { title: 'ICJ proceedings on legality of Israeli occupation draw global attention', publisher: 'The Guardian' },
      { title: 'Pentagon approves new weapons package for Israel amid criticism', publisher: 'Washington Post' },
      { title: 'South Africa leads global south in condemning Gaza operations', publisher: 'Daily Maverick' },
    ],
    source_count: 680,
    top_sources: ['BBC', 'CNN', 'Al Jazeera', 'Reuters', 'AFP', 'NYT', 'The Guardian', 'Times of Israel'],
    publisher_count: 190,
    publisher_hhi: 0.015,
    language_count: 18,
    language_distribution: { en: 350, ar: 80, he: 40, fr: 35, de: 30, es: 28, tr: 20, pt: 18, id: 15, ur: 12, fa: 12, it: 10, nl: 8, ja: 7, ko: 5, ms: 5, zh: 3, ru: 2 },
  },
];

// ---- Build prompt (mirrors rai-engine.ts buildAnalysisPrompt with new modules) ----
function buildTestPrompt(c: TestCase): string {
  const parts: string[] = [];

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
    '**GEOPOLITICAL CONTEXT:**',
    `Region: ${c.centroid_name}`,
    `Track: ${c.track}`,
    `Event: ${c.event_title}`,
    '',
    '**NARRATIVE FRAME UNDER ANALYSIS:**',
    `Label: ${c.narrative_label}`,
    `Moral Frame: ${c.moral_frame}`,
    `Description: ${c.description}`,
    `Source Count: ${c.source_count}`,
    `Top Sources: ${c.top_sources.join(', ')}`,
    '',
    '**COVERAGE STATISTICS:**',
    `- ${c.publisher_count} publishers, concentration index (HHI): ${c.publisher_hhi.toFixed(3)} (0=diverse, 1=monopoly)`,
    `- ${c.language_count} languages: ${Object.entries(c.language_distribution).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([l, n]) => `${l} ${Math.round(n / c.source_count * 100)}%`).join(', ')}`,
    '',
    '**SAMPLE HEADLINES:**',
  );
  for (const h of c.sample_titles) {
    parts.push(`- "${h.title}" (${h.publisher})`);
  }
  parts.push('');

  // -- CL-0 (core) --
  parts.push(
    '**SELECTED RAI ANALYSIS COMPONENTS:**',
    '',
    '**Execution Order:** CL-0 -> CL-6 -> NL-3 -> SL-8 -> CL-7',
    '',
    '---',
    '',
    '**CL-0: Narrative Contextualization and Framing Assessment**',
    '*Purpose:* Contextualize the narrative frame within the broader event and assess its framing strategy.',
    '',
    '*Core Questions:*',
    '- How does this narrative frame position itself relative to the broader event?',
    '- What framing choices (emphasis, omission, moral anchoring) shape this narrative?',
    '- What does the moral simplification reveal about the source ecosystem producing it?',
    '- Are there factual, narrative, or systemic components being conflated or separated?',
    '',
    '*Philosophical Anchoring:*',
    '- **D1.1**: Power is rarely surrendered; it is redistributed through ritual, consensus, or coercion.',
    '- **D6.2**: Moral certainty often masks geopolitical or institutional interests. The language of "values" and "human rights" is frequently used to cloak strategic motives.',
    '',
    '---',
    '',
    // -- CL-6 (NEW - core) --
    '**CL-6: Material Impact Grounding**',
    '*Purpose:* Establish verified material facts (actions, casualties, destruction, sovereignty violations) before evaluating narrative framing. Distinguish proportionate reaction from strategic amplification. Anchor critical analysis in physical reality.',
    '',
    '*Core Questions:*',
    '- What physical actions are confirmed across multiple independent source chains (not just multiple brands in the same bloc)?',
    '- What is the scale of material harm -- deaths, destruction, territorial change, leadership elimination?',
    '- Is the narrative reaction proportionate to the verified material impact, or is it amplified/minimized?',
    '- Where does confirmed material fact end and interpretive framing begin?',
    '',
    '*Philosophical Anchoring:*',
    '- **D2.8**: Material damage is not a narrative -- it is a fact that precedes interpretation. Before deconstructing how an event is framed, establish what physically occurred. Verified destruction, death, sovereignty violation, or assassination carries inherent weight that critical analysis cannot deconstruct away. A bombed capital is not a "framing choice." A killed leader is not a "narrative strategy." Confusing proportionate reaction with strategic manipulation is itself a form of analytical distortion.',
    '- **D2.9**: Kinetic action and structural position can point in opposite directions. The party advancing militarily may be the party structurally besieged. The party absorbing strikes may be applying long-term systemic pressure. Collapsing "who is shooting" into "who is the aggressor" produces shallow analysis.',
    '- **D6.1**: Multiple value systems can be valid within their own logic.',
    '',
    '*Wisdom Guidance:*',
    '- *A bombed city does not need a narrative to be real.*',
    '- *Deconstruction without grounding is intellectual entertainment.*',
    '- *Proportionality is the bridge between fact and framing.*',
    '',
    '---',
    '',
    // -- NL-3 (core) --
    '**NL-3: Competing Narratives Contrast**',
    '*Purpose:* Surface alternative narratives to evaluate blind spots, cultural framings, or missing dimensions.',
    '',
    '*Core Questions:*',
    '- What other groups or actors interpret this differently?',
    '- What facts do those narratives emphasize or ignore?',
    '- Are they mutually exclusive or potentially synthesizable?',
    '- Who benefits from each version?',
    '',
    '---',
    '',
    // -- SL-8 (core) --
    '**SL-8: Systemic Blind Spots and Vulnerabilities**',
    '*Purpose:* Reveal what the system or dominant information flow cannot process -- its blind spots, silences, or forbidden truths.',
    '',
    '*Core Questions:*',
    '- What facts or arguments are persistently excluded?',
    '- What questions cannot be asked in polite society?',
    '- What knowledge is penalized?',
    '',
    '---',
    '',
    // -- CL-7 (NEW - selected for all test cases) --
    '**CL-7: Coverage Ecosystem Diagnosis**',
    '*Purpose:* Assess whether source diversity metrics reflect genuine epistemic independence or bloc-level narrative alignment. Identify structurally absent perspectives and estimate what the coverage gap conceals.',
    '',
    '*Core Questions:*',
    '- Do high publisher/language counts reflect independent information chains or aligned bloc amplification?',
    '- Which actors, regions, or perspectives are structurally absent from the source ecosystem?',
    '- Are non-aligned or isolated sources being dismissed by mechanical diversity metrics?',
    '- What would the narrative look like if the invisible side had equal media reach?',
    '',
    '*Philosophical Anchoring:*',
    '- **D3.6**: Structural diversity is not epistemic diversity. A hundred voices speaking in harmony are one voice amplified. Large media ecosystems can exhibit high statistical diversity while sharing upstream information chains. True source independence is measured not by brand count but by the independence of originating information and by willingness to carry narratives that contradict bloc consensus.',
    '- **D3.1**: Information is a commodity in peace and a weapon in systemic conflict.',
    '- **D2.6**: Geopolitical behavior is shaped by enduring asymmetries.',
    '',
    '*Wisdom Guidance:*',
    '- *Count the voices, then check if they share a throat.*',
    '- *Absence of coverage is not absence of reality.*',
    '- *The loudest room is not the most informed.*',
    '',
    '---',
    '',
  );

  // Output format
  parts.push(
    '**OUTPUT FORMAT INSTRUCTIONS:**',
    '- Use `## ` (h2) for each module heading (e.g., ## CL-0: Narrative Contextualization)',
    '- Use bullet lists for findings and blind spots',
    '- Keep each section to 2-4 paragraphs max',
    '- Mark philosophical insights with `> ` blockquote syntax',
    '- Use `### ` (h3) for sub-sections within a module if needed',
    '',
    'When referencing RAI premises (D1.1, D2.5, etc.), always explain what the premise says inline rather than just citing the ID. The reader does not have access to the premise library.',
    '',
    '**At the end of your analysis**, output a scoring block in this exact format:',
    '',
    'SCORES: {"adequacy": <0.0-1.0>, "bias_detected": <0.0-1.0>, "coherence": <0.0-1.0>, "evidence_quality": <0.0-1.0>, "blind_spots": ["...", "..."], "conflicts": ["...", "..."], "synthesis": "<1-2 sentence summary>"}',
    '',
    'The scores must reflect your actual analysis. Do NOT use placeholder values.',
  );

  return parts.join('\n');
}

// ---- Call DeepSeek ----
async function callDeepSeek(prompt: string): Promise<string> {
  const res = await fetch(API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${API_KEY}`,
    },
    body: JSON.stringify({
      model: MODEL,
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.3,
      max_tokens: 4000,
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`DeepSeek API error ${res.status}: ${text.slice(0, 300)}`);
  }

  const data = await res.json() as any;
  return data.choices?.[0]?.message?.content || '(empty response)';
}

// ---- Main ----
async function main() {
  const outDir = path.resolve(__dirname, '../out/rai_test');
  fs.mkdirSync(outDir, { recursive: true });

  for (const c of CASES) {
    const slug = c.name.toLowerCase().replace(/[^a-z0-9]+/g, '_');
    console.log(`\n=== ${c.name} ===`);

    const prompt = buildTestPrompt(c);

    // Save prompt for inspection
    fs.writeFileSync(path.join(outDir, `${slug}_prompt.txt`), prompt);
    console.log(`  Prompt saved (${prompt.length} chars)`);

    console.log('  Calling DeepSeek...');
    const t0 = Date.now();
    const result = await callDeepSeek(prompt);
    const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
    console.log(`  Response received (${result.length} chars, ${elapsed}s)`);

    fs.writeFileSync(path.join(outDir, `${slug}_result.md`), result);
    console.log(`  Result saved to out/rai_test/${slug}_result.md`);
  }

  console.log('\nDone. All results in out/rai_test/');
}

main().catch(console.error);
