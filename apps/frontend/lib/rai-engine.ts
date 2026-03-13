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

// ---- Premises (54) -------------------------------------------------------

const PREMISE_LIBRARY: Record<string, { title: string; content: string }> = {
  // D1: Power & Governance
  'D1.1': {
    title: 'Power is rarely surrendered; it is redistributed through ritual, consensus, or coercion',
    content: 'In all functioning systems -- democratic, autocratic, or hybrid -- true power shifts occur under one of three conditions: Elite consensus to preserve stability, External pressure or control, or Systemic fracture or collapse. Elections and constitutional processes are often choreographed simulations to legitimize decisions already negotiated behind closed doors.',
  },
  'D1.2': {
    title: 'Political actors emerge from their cultural substrate',
    content: 'Politicians are neither a separate species nor inherently corrupt -- they reflect the ambitions, fears, and incentives of their societal base. While some act from self-interest, others assume genuine stewardship of national projects. Systems produce the leaders they enable, and demonizing individuals obscures structural flaws or popular complicity.',
  },
  'D1.3': {
    title: 'Power is sustained through economic architecture',
    content: 'Control over capital flows, debt, resource distribution, and media ownership often underlies political stability more than formal institutions or laws. Ownership replaces force, creating systemic compliance even in "free" societies.',
  },
  'D1.4': {
    title: 'International law and institutions are instruments of power, not neutral arbiters',
    content: 'The UN Security Council, ICC, WTO, and IMF were designed by post-WWII victors and reflect their structural interests. Selective enforcement is not an aberration but a feature: some leaders are indicted while others enjoy impunity, some invasions trigger sanctions while others receive diplomatic cover. The phrase "rules-based order" itself is a narrative that privileges those who wrote the rules. Media coverage that invokes "international law" as an objective standard without examining whose law, enforced by whom, and against whom, is performing advocacy disguised as reporting.',
  },
  // D2: Geopolitical Order & Conflict
  'D2.1': {
    title: 'A few powers shape the planetary game',
    content: 'Despite the appearance of multilateralism, geopolitical outcomes are determined by a small number of dominant states or blocs. Smaller actors either align with these poles, operate as regional proxies, or are marginalized.',
  },
  'D2.2': {
    title: 'Systemic war is ongoing, with kinetic conflict as its loudest symptom',
    content: 'Economic pressure, cyberattacks, and narrative domination are integral tools of modern conflict. Physical war is no longer the beginning of conflict, but its explosion point.',
  },
  'D2.3': {
    title: 'Neutrality becomes illusion in systemic conflict',
    content: 'In high-stakes global competition, all states are drawn into alignment, either through dependence, coercion, or survival instinct. True neutrality is impossible in a deeply interconnected world.',
  },
  'D2.4': {
    title: 'Nuclear weapons enforce adult behavior through existential fear',
    content: 'The doctrine of Mutual Assured Destruction (MAD) has replaced idealism as the real guarantor of peace. Disarmament is noble, but premature. Without existential threat, aggressive competition would likely lead to catastrophe.',
  },
  'D2.5': {
    title: 'War is waged beneath the surface through deception and engineered ambiguity',
    content: 'Modern power projection often hides behind peace initiatives, democratic rhetoric, or defensive postures. Narratives become masks for strategic aims, enabling operations without triggering open conflict.',
  },
  'D2.6': {
    title: 'Geopolitical behavior is shaped by enduring asymmetries',
    content: 'Power disparities in media reach, military capabilities, economic leverage, human resources, or technological infrastructure define what actors can realistically do.',
  },
  'D2.7': {
    title: 'Strategic interests are survival logic dressed in moral clothing',
    content: 'Behind every noble speech about peace and values is a spreadsheet calculating market access, resource control, and strategic leverage. States act not out of virtue, but necessity -- or appetite. Moral narratives are often retrofitted onto strategic decisions.',
  },
  'D2.8': {
    title: 'Material damage is not a narrative -- it is a fact that precedes interpretation',
    content: 'Before deconstructing how an event is framed, establish what physically occurred. Verified destruction, death, sovereignty violation, or assassination carries inherent weight that critical analysis cannot deconstruct away. A bombed capital is not a "framing choice." A killed leader is not a "narrative strategy." Confusing proportionate reaction with strategic manipulation is itself a form of analytical distortion. The critical apparatus must be anchored in material reality, or it degenerates into cynicism.',
  },
  'D2.9': {
    title: 'Kinetic action and structural position can point in opposite directions',
    content: 'The party advancing militarily may be the party structurally besieged -- acting from encirclement, existential threat, or accumulated provocation. The party absorbing strikes may simultaneously be the party applying long-term systemic pressure through alliances, sanctions, or expansion. Collapsing "who is shooting" into "who is the aggressor" produces shallow analysis. Adequate assessment requires examining kinetic reality, structural position, and historical sequence independently before synthesis.',
  },
  'D2.10': {
    title: 'Sanctions are economic warfare with civilian casualties',
    content: 'Economic sanctions, SWIFT exclusion, asset freezes, and trade embargoes cause measurable civilian harm -- hunger, medical shortages, infrastructure collapse, excess mortality -- but are narratively positioned as "peaceful alternatives to military action." Media coverage systematically separates the imposition of sanctions from their human cost, treating the policy decision as news and the suffering as background. This framing asymmetry allows economic siege to escape the moral scrutiny applied to kinetic warfare. Adequate analysis must treat sanctions as a form of force and audit their consequences with the same rigor applied to military operations.',
  },
  // D3: Information & Perception
  'D3.1': {
    title: 'Information is a commodity in peace and a weapon in systemic conflict',
    content: 'In peacetime, information flows are monetized; in systemic conflict, they are weaponized. Media must be controlled -- whether through ownership, funding, surveillance, or subtle incentivization. Truly "free" or "independent" media is a functional myth, not a structural reality.',
  },
  'D3.2': {
    title: 'Censorship and visibility are asymmetric tools',
    content: 'Control over digital infrastructure -- platforms, algorithms, recommendation engines, content policies -- enables nonlinear narrative dominance. What is suppressed is often less important than what is invisibly sidelined.',
  },
  'D3.3': {
    title: 'Perception is power',
    content: 'Legitimacy, victimhood, and moral high ground are not just narratives -- they are operational assets. Winning the story often has greater strategic value than winning the terrain. Modern information warfare includes memetic injection, coordinated emotional framing, information flooding, and virality engineering.',
  },
  'D3.4': {
    title: 'Thought policing outperforms censorship',
    content: 'When populations internalize the boundaries of acceptable thought, external repression becomes redundant. Self-censorship, social penalty, and digital panopticism are more effective than coercive force.',
  },
  'D3.5': {
    title: 'Large-scale protests are rarely spontaneous',
    content: 'Mass participation may appear organic, but major movements that gain traction nearly always rest on pre-existing infrastructure: trained organizers, aligned institutions, sympathetic media, and international funding streams.',
  },
  'D3.6': {
    title: 'Structural diversity is not epistemic diversity',
    content: 'A hundred voices speaking in harmony are one voice amplified. Large media ecosystems -- spanning multiple countries, languages, and brands -- can exhibit high statistical diversity while sharing upstream information chains (wire services, intelligence briefings, editorial assumptions). True source independence is measured not by brand count but by the independence of originating information and by willingness to carry narratives that contradict bloc consensus. Isolated or non-aligned media nodes may appear "one-sided" by mechanical metrics precisely because they lack allied amplification networks -- not because their content is less factual.',
  },
  'D3.7': {
    title: 'The language of description is itself a framing device',
    content: 'Before any opinion is offered, the vocabulary of supposedly neutral reporting pre-encodes judgment. "Regime" vs "government," "militant" vs "fighter," "annexation" vs "reunification," "intervention" vs "invasion" -- these choices establish moral orientation before the reader reaches the editorial line. The most effective framing is invisible: it lives in word selection, not in argument. Media analysis that audits explicit claims but accepts descriptive vocabulary at face value misses the deepest layer of bias.',
  },
  // D4: Civilization & Culture
  'D4.1': {
    title: 'Cultural self-image distorts memory',
    content: 'Societies tend to idealize their past, suppressing atrocities, defeats, or failures. Collective memory is selectively curated through trauma editing, symbolic purification, and ritualized storytelling in education, monuments, and national holidays.',
  },
  'D4.2': {
    title: 'Victimhood is political capital',
    content: 'Groups and nations frame themselves as historical victims to gain legitimacy, immunize against criticism, and mobilize internal cohesion or international sympathy. These narratives often blur genuine trauma with instrumental storytelling.',
  },
  'D4.3': {
    title: 'Civilizations pursue different visions of success',
    content: 'All cultures strive for stability, continuity, and influence -- but their definitions of success vary profoundly. Some prioritize expansion or technological progress; others value harmony, survival, or spiritual legacy. Judging them by a single universal standard often reflects ideological projection, not objective analysis.',
  },
  'D4.4': {
    title: 'Cultural soft power is a vector of dominance',
    content: 'Narratives travel through film, entertainment, humanitarian aid, and globalized education. Cultural output becomes a carrier of ideology, shaping aspiration, moral hierarchies, and political alignment.',
  },
  'D4.5': {
    title: 'Culture encodes strategy',
    content: 'Deep-seated cultural traits -- whether collectivist or individualist, honor-based or legality-based -- shape behavior in diplomacy, warfare, and negotiation. What seems irrational to outsiders may follow a coherent internal logic.',
  },
  'D4.6': {
    title: 'Civilizational universalism is projection, not discovery',
    content: 'What passes for "universal values" -- human rights, democratic governance, individual liberty, market freedom -- has a specific genealogy: Enlightenment European philosophy, post-1945 American institutional design, Cold War ideological competition. These values are not inherently wrong, but their claim to universality obscures their origin and serves the interests of civilizations with the greatest narrative reach. Media coverage that treats Western liberal norms as the neutral baseline from which all deviations are measured is not reporting -- it is civilizational advocacy. Adequate analysis examines whose universalism is being applied and what it displaces.',
  },
  // D5: System Dynamics & Complexity
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
  'D5.4': {
    title: 'Self-correction requires pressure valves',
    content: 'Resilient systems create mechanisms of controlled release: courts, protests, satire, journalism. When these are co-opted or blocked, pressure accumulates and can explode.',
  },
  'D5.5': {
    title: 'Narratives are the software of systems',
    content: 'The shared stories people believe about their system enable it to function. When narratives degrade, the system behavioral code becomes corrupted. Crises of legitimacy are often preceded by narrative entropy.',
  },
  'D5.6': {
    title: 'Complex systems produce outcomes no actor intended or controls',
    content: 'Global finance, migration flows, pandemic spread, climate feedback, and arms races generate emergent results that cannot be attributed to any single conspiracy or plan. Yet media narratives demand identifiable villains and heroes -- collapsing systemic causation into personal agency. Both conspiratorial over-attribution ("they planned this") and naive agency-denial ("nobody is responsible") fail the complexity test. Adequate analysis must sit with irreducible causal ambiguity: multiple actors contributing to outcomes none of them fully designed, in systems none of them fully control.',
  },
  // D6: Ethics & Judgment
  'D6.1': {
    title: 'Multiple value systems can be valid within their own logic',
    content: 'Different ethical traditions -- religious, cultural, strategic -- can produce conflicting judgments without either being objectively false. What is "just" in one worldview may be "barbaric" in another. Ethical analysis requires context, not universalization.',
  },
  'D6.2': {
    title: 'Moral certainty often masks geopolitical or institutional interests',
    content: 'The language of "values" and "human rights" is frequently used to cloak strategic motives. Claiming virtue becomes a tool of leverage, especially when paired with sanctions, military action, or selective outrage.',
  },
  'D6.3': {
    title: 'The oppressed often inherit and reenact the logic of the oppressor',
    content: 'Those who once suffered injustice may replicate coercive systems when power shifts. Victimhood does not guarantee virtue, and sympathy should never replace structural scrutiny.',
  },
  'D6.4': {
    title: 'Democratic decay often originates from the people, not just elites',
    content: 'While corruption and manipulation matter, mass apathy, fear, and ignorance can also erode democratic life. When the public ceases to demand virtue, representation becomes spectacle.',
  },
  'D6.5': {
    title: 'Political virtue is often the retroactive moralization of success',
    content: 'History is written by winners, and legitimacy is often post-facto storytelling. What is framed as noble leadership may be little more than effective domination rewritten in moral terms.',
  },
  'D6.6': {
    title: 'Hypocrisy is not an anomaly, but a structural feature of moral discourse',
    content: 'Nations, institutions, and individuals often fail to meet the standards they preach -- not merely from weakness, but because moral language is strategically deployed to manage perception, not guide consistent behavior.',
  },
  // D7: Temporal Awareness & Strategic Foresight
  'D7.1': {
    title: 'Historical context is essential for understanding motivation',
    content: 'Current decisions reflect accumulated trauma, inherited grievances, and strategic memory. Nations and actors often pursue goals laid down by events decades -- or centuries -- earlier. Analyzing current actions without their temporal roots produces shallow or false interpretations.',
  },
  'D7.2': {
    title: 'Delayed outcomes are often more impactful than immediate ones',
    content: 'What seems like success in the short term may erode legitimacy or stability over time. Systems have latency, and interventions often unleash feedback loops that manifest far later. Strategic judgment demands temporal patience.',
  },
  'D7.3': {
    title: 'History rewards the effective, not the grateful',
    content: 'There is no durable currency of gratitude in international relations or political history. Alliances shift based on interest, not memory. Attempts to extract loyalty based on past aid or sacrifice usually fail.',
  },
  'D7.4': {
    title: 'Civilizations rise and fall in cycles',
    content: 'No system lasts forever. Civilizations experience arcs of emergence, dominance, stagnation, and collapse. Denial of this cycle leads to strategic complacency and hubris.',
  },
  'D7.5': {
    title: 'The future is colonized by today\'s narratives',
    content: 'The stories we tell about the future -- progress, collapse, justice, revenge -- shape policy, science, investment, and war. Competing visions of the future often drive present action more than actual planning does.',
  },
  'D7.6': {
    title: 'Strategic actors plan in decades; reactive actors respond in headlines',
    content: 'Global competition rewards those who think beyond the electoral cycle or news cycle. Systems with long memory and long-range planning shape outcomes more decisively than populist turbulence.',
  },
  'D7.7': {
    title: 'Delays between cause and effect conceal responsibility',
    content: 'When consequences unfold years later, those who set events in motion often escape accountability. Strategic manipulation benefits from this delay, enabling actors to externalize blame while pursuing short-term gain.',
  },
  // D8: Political Economy & Resource Power
  'D8.1': {
    title: 'Economic power precedes and shapes political outcomes',
    content: 'The distribution of capital, land, labor, and credit forms the invisible scaffolding beneath political institutions. Governance structures often emerge as reflections of dominant economic interests.',
  },
  'D8.2': {
    title: 'Class remains a functional reality beneath changing labels',
    content: 'Despite rhetorical progress or rebranding, societies continue to stratify along lines of control over productive assets. Whether under capitalism, state socialism, or mixed regimes, there is always a division between those who own, those who manage, and those who labor.',
  },
  'D8.3': {
    title: 'Resource dependencies define strategic behavior',
    content: 'Access to energy, rare materials, food, and water determines national security and foreign policy alignment. States will violate ethical norms or destabilize entire regions to secure such resources.',
  },
  'D8.4': {
    title: 'Debt is a tool of control, not just finance',
    content: 'Public and private debt create long-term dependency structures. Lenders can shape policy, impose austerity, and dictate reforms under the guise of fiscal discipline or development assistance.',
  },
  'D8.5': {
    title: 'Technology is not neutral -- it encodes power relations',
    content: 'Digital platforms, algorithmic finance, and data monopolies allow unprecedented economic concentration. The illusion of decentralization often masks deeper centralization in the hands of those who build and own the infrastructure.',
  },
  'D8.6': {
    title: 'Labor is globalized, devalued, and fragmented',
    content: 'In a globalized economy, labor no longer negotiates from a national base. Jobs are offshored, gigified, or automated. As collective bargaining weakens, workers become interchangeable, and economic insecurity becomes a tool of control.',
  },
  'D8.7': {
    title: 'Automation shifts power from labor to capital',
    content: 'As machines replace human labor, value concentrates around intellectual property, infrastructure ownership, and data extraction. Automation does not eliminate labor -- it transforms it into invisible maintenance and algorithmic obedience.',
  },
  'D8.8': {
    title: 'Supply chains are strategic weapons',
    content: 'Global trade networks are not just economic artifacts -- they are levers of pressure in geopolitical struggle. Countries that control logistics chokepoints, manufacturing hubs, or rare-earth refining can extract political concessions without firing a shot.',
  },
};

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
