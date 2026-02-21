// ---------------------------------------------------------------------------
// RAI Engine -- local prompt builder, DeepSeek caller, response parser
// Replaces the RAI Render intermediary for WorldBrief narrative analysis.
// ---------------------------------------------------------------------------

import type { SignalStats } from '@/lib/types';

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

// ---- Premises (46) -------------------------------------------------------

const PREMISE_LIBRARY: Record<string, RaiPremise> = {
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

// ---- Modules (33) -- keyed by ID for lookup after selection ----------------

const MODULE_LIBRARY: Record<string, RaiModule> = {
  // -- Cross-Level (CL) --
  'CL-0': {
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
  'CL-1': {
    id: 'CL-1',
    name: 'Narrative Logic Compression',
    purpose: 'Trace how individual facts are being linked into narrative arcs -- and identify compression, distortion, or omission in that linkage.',
    core_questions: [
      'Are facts cherry-picked or overpacked?',
      'Are connections between events natural or forced?',
      'Are narrative arcs formed by implication instead of logic?',
      'What causal assumptions are embedded in the story structure?',
    ],
    wisdom_injected: [
      'Narrative is the space between facts.',
      'Compression is the birthplace of distortion.',
      'What connects may also disconnect.',
    ],
    philosophical_anchoring: ['D1.3', 'D4.1', 'D7.2'],
  },
  'CL-2': {
    id: 'CL-2',
    name: 'Epistemic Load Balance',
    purpose: 'Test how knowledge burdens are distributed: What is assumed vs. what is proven? What must the audience infer, accept, or ignore?',
    core_questions: [
      'What "common sense" is assumed?',
      'Are any critical elements left implicit?',
      'Does the burden of proof fall unfairly on one side?',
      'What knowledge gaps are being papered over?',
    ],
    wisdom_injected: [
      'What\'s not said may cost more than what is.',
      'A rigged narrative hides its load.',
      'Assumptions are the invisible architecture of argument.',
    ],
    philosophical_anchoring: ['D2.2', 'D6.6'],
  },
  'CL-3': {
    id: 'CL-3',
    name: 'Narrative Stack Tracking',
    purpose: 'Map layered or nested narratives -- how facts support storylines, which support ideologies, which support strategic goals.',
    core_questions: [
      'What deeper story does this surface claim support?',
      'How many layers deep does the logic go?',
      'Are meta-narratives functioning as shields or amplifiers?',
      'Which narrative layer is doing the real work?',
    ],
    wisdom_injected: [
      'Some stories wear other stories like armor.',
      'The first claim is often the bait.',
      'Depth reveals direction.',
    ],
    philosophical_anchoring: ['D4.2', 'D6.3', 'D7.1'],
  },
  'CL-4': {
    id: 'CL-4',
    name: 'Moral and Strategic Fusion Detection',
    purpose: 'Identify moments where moral language is fused with strategic logic to mask real motivations or trigger tribal response.',
    core_questions: [
      'Are moral claims used to justify strategic actions?',
      'Is moral framing exaggerated to obscure realism?',
      'What would the statement sound like if stripped of moral charge?',
      'Does virtue signaling serve strategic functions?',
    ],
    wisdom_injected: [
      'Moral words win wars -- on screens.',
      'Look where the virtue points -- then follow the money.',
      'Strategic necessity wears moral clothing.',
    ],
    philosophical_anchoring: ['D6.2', 'D6.4', 'D6.5'],
  },
  'CL-5': {
    id: 'CL-5',
    name: 'Evaluative Symmetry Enforcement',
    purpose: 'Ensure actors, events, or claims are judged by consistent standards -- even if they belong to different camps, cultures, or ideologies.',
    core_questions: [
      'Would this action be praised or condemned if done by the other side?',
      'Are similar acts being framed in opposite ways?',
      'Is the framework itself being bent to spare allies?',
      'What would neutral evaluation look like?',
    ],
    wisdom_injected: [
      'If it\'s wrong for them, it\'s wrong for you.',
      'Truth wears no uniform.',
      'Consistency is the test of principle.',
    ],
    philosophical_anchoring: ['D2.1', 'D6.1', 'D3.3'],
  },
  // -- Fact-Level (FL) --
  'FL-1': {
    id: 'FL-1',
    name: 'Claim Clarity and Anchoring',
    purpose: 'Isolate and verify the core factual claims. Ensure each is specific, testable, and anchored in time/place.',
    core_questions: [
      'What exactly is being claimed -- and is it stated as a fact?',
      'Is it time-stamped and location-bound?',
      'Is it observable or measurable?',
      'Is it distorted by metaphor or emotional language?',
    ],
    wisdom_injected: [
      'Epistemic humility: Flag unverifiables, don\'t guess.',
      'Linguistic precision: Strip rhetoric, keep signal.',
      'Facts live in time and space.',
    ],
    philosophical_anchoring: ['D1.1', 'D1.2', 'D2.1'],
  },
  'FL-2': {
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
  'FL-3': {
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
  'FL-4': {
    id: 'FL-4',
    name: 'Strategic Relevance and Selection',
    purpose: 'Evaluate whether a fact is strategically chosen to steer perception or obscure larger realities.',
    core_questions: [
      'Is the fact central to the story or a distraction?',
      'Would omitting this fact mislead? Would adding a suppressed one clarify?',
      'Is it cherry-picked to create a false narrative?',
      'What does the selection pattern reveal about intent?',
    ],
    wisdom_injected: [
      'The truth may be in what\'s unsaid.',
      'Strategic omission is the most elegant lie.',
      'Selection reveals intention.',
    ],
    philosophical_anchoring: ['D4.2', 'D7.2', 'D8.2'],
  },
  'FL-5': {
    id: 'FL-5',
    name: 'Scale and Proportion Calibration',
    purpose: 'Prevent inflation or minimization of facts through poor scale framing.',
    core_questions: [
      'Is this fact being framed as exceptional or representative?',
      'Are numbers proportionate or manipulated by percent, scope, or baseline?',
      'Would this framing hold across equivalent cases?',
      'What does proper contextualization reveal?',
    ],
    wisdom_injected: [
      'Big data can lie small, and small facts can scream.',
      'Context is the compass of honesty.',
      'Scale without context is manipulation.',
    ],
    philosophical_anchoring: ['D1.2', 'D1.3', 'D8.1'],
  },
  'FL-6': {
    id: 'FL-6',
    name: 'Neglected Primary Speech Recognition',
    purpose: 'Identify whether primary actor statements have been omitted or misrepresented.',
    core_questions: [
      'Has the subject of the claim spoken directly on the matter?',
      'Are those statements missing, cherry-picked, or distorted?',
      'What would direct quotes reveal that paraphrases hide?',
      'Why might primary speech be avoided or filtered?',
    ],
    wisdom_injected: [
      'Let them speak -- then check the echo.',
      'Silencing someone by paraphrase is still silencing.',
      'Primary speech reveals primary intent.',
    ],
    philosophical_anchoring: ['D2.3', 'D3.1', 'D6.1'],
  },
  'FL-7': {
    id: 'FL-7',
    name: 'Risk Context Adjustment',
    purpose: 'Tune skepticism based on stakes. Differentiate casual errors from high-stakes manipulations.',
    core_questions: [
      'Is this claim embedded in a low-risk or high-risk topic (e.g., war, finance, biopolitics)?',
      'Do the consequences of falsehood justify higher scrutiny?',
      'What interests are served by belief or disbelief?',
      'How does risk level affect evidentiary standards?',
    ],
    wisdom_injected: [
      'The higher the cost of the lie, the deeper you dig.',
      'Low-risk truths may not deserve your time. High-risk lies always do.',
      'Stakes determine standards.',
    ],
    philosophical_anchoring: ['D7.2', 'D8.3', 'D8.5'],
  },
  'FL-8': {
    id: 'FL-8',
    name: 'Time & Place Anchoring',
    purpose: 'Ensure all factual claims are tied to specific, verifiable moments and locations.',
    core_questions: [
      'Is there a clear timestamp and identifiable location?',
      'Are those consistent with known records or conflicting claims?',
      'Is ambiguity being used to protect from accountability?',
      'What does temporal-spatial precision reveal or conceal?',
    ],
    wisdom_injected: [
      'Truth lives in time. Lies float.',
      'No fact should be homeless.',
      'Precision prevents manipulation.',
    ],
    philosophical_anchoring: ['D1.2', 'D7.1', 'D7.4'],
  },
  'FL-9': {
    id: 'FL-9',
    name: 'Toxic Label Audit',
    purpose: 'Detect and neutralize judgment-distorting terms like "conspiracy theory," "populist," or "authoritarian regime" that may preempt empirical evaluation.',
    core_questions: [
      'Is the claim being disqualified due to who says it rather than what is said?',
      'Are rhetorical labels replacing evidence or logic?',
      'Does the claim violate reality, or just elite preferences?',
      'What happens when we strip away the labels and examine the substance?',
    ],
    wisdom_injected: [
      'Adequacy trumps acceptability.',
      'A claim\'s origin does not determine its validity.',
      'Ideological hygiene is not a proxy for truth.',
    ],
    philosophical_anchoring: ['D2.1', 'D3.3', 'D6.5'],
  },
  // -- Narrative-Level (NL) --
  'NL-1': {
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
  'NL-2': {
    id: 'NL-2',
    name: 'Narrative Plausibility & Internal Coherence',
    purpose: 'Test the story\'s internal logic, character consistency, and plausibility without external verification.',
    core_questions: [
      'Do events follow naturally within the narrative?',
      'Are motivations consistent with known actor behavior?',
      'Are narrative contradictions explained or ignored?',
      'Does the story require magical thinking or implausible leaps?',
    ],
    wisdom_injected: [
      'Even lies must make sense -- if they don\'t, question harder.',
      'Inconsistency is often the fingerprint of fiction.',
    ],
    philosophical_anchoring: ['D1.3', 'D4.1', 'D6.1'],
  },
  'NL-3': {
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
  'NL-4': {
    id: 'NL-4',
    name: 'Identity, Memory, and Group Interest Framing',
    purpose: 'Identify how group identities, historical trauma, and loyalty shape narrative preference and perception.',
    core_questions: [
      'What group identities are centered, valorized, or demonized?',
      'Are historical grievances reactivated?',
      'How is loyalty framed: as honor, duty, betrayal, or survival?',
      'What moral or symbolic rewards are attached to belief?',
    ],
    wisdom_injected: [
      'We see through the stories we inherit.',
      'Group truth is not whole truth.',
    ],
    philosophical_anchoring: ['D3.1', 'D6.3', 'D7.1'],
  },
  'NL-5': {
    id: 'NL-5',
    name: 'Allegory, Analogy, and Symbol Injection',
    purpose: 'Flag where metaphor, analogy, or symbolism is distorting clarity or smuggling ideology.',
    core_questions: [
      'Are historical analogies accurate or manipulative?',
      'Are symbols used to oversimplify or moralize?',
      'Does the analogy illuminate -- or obscure -- the situation?',
      'What emotional payload is the metaphor carrying?',
    ],
    wisdom_injected: [
      'Symbols short-circuit thinking when unchecked.',
      'Not all rhymes in history are honest.',
    ],
    philosophical_anchoring: ['D1.3', 'D4.2', 'D6.2'],
  },
  'NL-6': {
    id: 'NL-6',
    name: 'Narrative Gaps',
    purpose: 'Identify what\'s missing from the story that would change interpretation or conclusion.',
    core_questions: [
      'What key actors, events, or timeframes are absent?',
      'Would including missing elements change the moral or causal assessment?',
      'Are gaps strategic omissions or natural limitations?',
      'What would a more complete picture reveal?',
    ],
    wisdom_injected: [
      'What\'s missing may matter more than what\'s present.',
      'Gaps are not accidents -- they are choices.',
    ],
    philosophical_anchoring: ['D4.1', 'D7.1', 'D3.2'],
  },
  // -- System-Level (SL) --
  'SL-1': {
    id: 'SL-1',
    name: 'Power and Incentive Mapping',
    purpose: 'Trace who benefits -- economically, politically, strategically -- from a given claim or interpretation.',
    core_questions: [
      'What actors gain material or symbolic advantage?',
      'Are the incentives aligned with claimed values?',
      'Are incentives obscured, denied, or misattributed?',
    ],
    wisdom_injected: [
      'Follow the gain, not the claim.',
      'Who benefits is not who speaks -- but who wins.',
    ],
    philosophical_anchoring: ['D5.1', 'D5.3', 'D8.2'],
  },
  'SL-2': {
    id: 'SL-2',
    name: 'Institutional Behavior and Enforcement Patterns',
    purpose: 'Examine how institutions (governments, media, NGOs) adopt, enforce, or suppress specific claims or framings.',
    core_questions: [
      'Are institutions aligned in promoting a particular position?',
      'Is dissent punished or discouraged?',
      'What control mechanisms (laws, funding, censure) are in play?',
    ],
    wisdom_injected: [
      'Institutions protect stories before people.',
      'Censorship is a form of narrative hygiene.',
    ],
    philosophical_anchoring: ['D5.2', 'D5.3', 'D8.3'],
  },
  'SL-3': {
    id: 'SL-3',
    name: 'Identity and Memory Exploitation',
    purpose: 'Uncover how collective memory, trauma, and identity are used to frame or justify current interpretations.',
    core_questions: [
      'What past events are invoked to legitimize the present?',
      'Are traumas weaponized or selectively remembered?',
      'Whose identity is being centered -- or erased?',
    ],
    wisdom_injected: [
      'The past is not dead -- it\'s rebranded.',
      'Memory is power disguised as history.',
    ],
    philosophical_anchoring: ['D3.1', 'D6.3', 'D7.1'],
  },
  'SL-4': {
    id: 'SL-4',
    name: 'Function and Purpose Analysis',
    purpose: 'Determine the deeper goal of a claim or framing -- mobilization, justification, distraction, polarization.',
    core_questions: [
      'What action does the message inspire or block?',
      'Is the goal moral, strategic, emotional, or institutional?',
      'Is the audience meant to feel, think, or act?',
    ],
    wisdom_injected: [
      'Messages are weapons with audiences as targets.',
      'Purpose reveals design -- even in lies.',
    ],
    philosophical_anchoring: ['D4.2', 'D4.4', 'D5.3'],
  },
  'SL-5': {
    id: 'SL-5',
    name: 'Systemic Resistance and Inversion',
    purpose: 'Detect if a claim resists dominant systems or mimics resistance while reinforcing the same structures.',
    core_questions: [
      'Is the framing genuinely oppositional or performative?',
      'Does it invert dominant logic or disguise it?',
      'Who adopts the resistance framing -- and why?',
    ],
    wisdom_injected: [
      'Not all rebels seek revolution. Some just want a turn at the throne.',
      'Inversion is not liberation.',
    ],
    philosophical_anchoring: ['D4.3', 'D5.3', 'D6.3'],
  },
  'SL-6': {
    id: 'SL-6',
    name: 'Feedback Systems and Loop Control',
    purpose: 'Identify recursive reinforcement loops that bias understanding, suppress contradiction, or simulate consensus.',
    core_questions: [
      'Are rebuttals systematically excluded?',
      'Do feedback channels reward loyalty over accuracy?',
      'Is dissent pathologized (e.g., labeled disloyal, irrational)?',
    ],
    wisdom_injected: [
      'What repeats, rules.',
      'Broken echo is still an echo.',
    ],
    philosophical_anchoring: ['D5.2', 'D7.3', 'D8.4'],
  },
  'SL-7': {
    id: 'SL-7',
    name: 'Strategic Forecast and Predictive Testing',
    purpose: 'Test the implications of claims by projecting future actions, outcomes, or contradictions.',
    core_questions: [
      'If the interpretation is true, what logically follows?',
      'Are predicted outcomes consistent with observed reality?',
      'Do real-world results falsify or validate the framing?',
    ],
    wisdom_injected: [
      'Truth has a trajectory.',
      'Prediction reveals what belief conceals.',
    ],
    philosophical_anchoring: ['D7.2', 'D7.4', 'D8.5'],
  },
  'SL-8': {
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
  'SL-9': {
    id: 'SL-9',
    name: 'Adaptive Evolution Awareness',
    purpose: 'Track how claims or framing evolve in response to public reaction, internal contradiction, or external pressure.',
    core_questions: [
      'Has the claim subtly shifted its framing?',
      'Are past claims abandoned or reinterpreted?',
      'Are inconsistencies explained or ignored?',
    ],
    wisdom_injected: [
      'The first draft of a lie often dies a hero.',
      'What adapts survives -- but not always with its soul.',
    ],
    philosophical_anchoring: ['D7.3', 'D7.4', 'D8.6'],
  },
  'SL-10': {
    id: 'SL-10',
    name: 'Feedback Loop Mapping and Distortion Patterns',
    purpose: 'Map and detect distortions in closed-loop information systems.',
    core_questions: [
      'Who inputs, moderates, and echoes information?',
      'Where does distortion occur and for what purpose?',
    ],
    wisdom_injected: [
      'Echo makes truth louder -- or drowns it.',
    ],
    philosophical_anchoring: ['D5.2', 'D7.3', 'D8.4'],
  },
  'SL-11': {
    id: 'SL-11',
    name: 'Technocratic Logic and Algorithmic Governance',
    purpose: 'Evaluate how algorithms, models, and technocratic claims shape or substitute political logic.',
    core_questions: [
      'What decisions are outsourced to systems?',
      'Are algorithmic claims used rhetorically?',
      'Does technical neutrality mask ideology?',
    ],
    wisdom_injected: [
      'What looks neutral may be coded.',
      'Math is not morality.',
    ],
    philosophical_anchoring: ['D5.3', 'D8.6', 'D8.7'],
  },
  'SL-12': {
    id: 'SL-12',
    name: 'Digital Infrastructure Control and Dependency',
    purpose: 'Assess how digital platforms, infrastructure, and dependencies shape strategic behavior and control over information.',
    core_questions: [
      'Who owns and governs the digital pipes?',
      'What happens if the infrastructure is withdrawn?',
      'Are dependencies used as leverage?',
    ],
    wisdom_injected: [
      'He who controls the pipe controls the pressure.',
    ],
    philosophical_anchoring: ['D5.2', 'D8.2', 'D8.7'],
  },
};

// ---- Module Catalog (compact, for selector prompt) ------------------------

const CORE_MODULE_IDS = ['CL-0', 'NL-3', 'SL-8'];
const FALLBACK_MODULE_IDS = ['NL-1', 'FL-2', 'FL-3'];

const MODULE_CATALOG: Array<{ id: string; summary: string }> = [
  { id: 'CL-1', summary: 'Trace fact-to-narrative linkage and compression distortion' },
  { id: 'CL-2', summary: 'Test assumption burden and hidden inference gaps' },
  { id: 'CL-3', summary: 'Map layered/nested narratives and meta-narrative shields' },
  { id: 'CL-4', summary: 'Detect moral language fused with strategic motives' },
  { id: 'CL-5', summary: 'Enforce consistent evaluation standards across all actors' },
  { id: 'FL-1', summary: 'Isolate, verify, and anchor core factual claims' },
  { id: 'FL-2', summary: 'Detect unnatural amplification or suppression patterns' },
  { id: 'FL-3', summary: 'Audit source independence, diversity, and coordination' },
  { id: 'FL-4', summary: 'Evaluate strategic fact selection and cherry-picking' },
  { id: 'FL-5', summary: 'Prevent scale inflation/minimization in fact framing' },
  { id: 'FL-6', summary: 'Identify omitted or misrepresented primary actor speech' },
  { id: 'FL-7', summary: 'Calibrate skepticism by stakes and risk context' },
  { id: 'FL-8', summary: 'Anchor claims in specific verifiable time and place' },
  { id: 'FL-9', summary: 'Detect judgment-distorting toxic labels' },
  { id: 'NL-1', summary: 'Evaluate cause-effect chain logic and start-point bias' },
  { id: 'NL-2', summary: 'Test narrative internal coherence and plausibility' },
  { id: 'NL-4', summary: 'Identify group identity and historical trauma framing' },
  { id: 'NL-5', summary: 'Flag distorting metaphors, analogies, and symbols' },
  { id: 'NL-6', summary: 'Identify strategic narrative gaps and omissions' },
  { id: 'SL-1', summary: 'Map power, incentive, and benefit structures' },
  { id: 'SL-2', summary: 'Examine institutional enforcement and suppression' },
  { id: 'SL-3', summary: 'Uncover collective memory and identity exploitation' },
  { id: 'SL-4', summary: 'Determine deeper purpose: mobilize, justify, distract' },
  { id: 'SL-5', summary: 'Detect performative resistance masking power structures' },
  { id: 'SL-6', summary: 'Identify recursive reinforcement loops and false consensus' },
  { id: 'SL-7', summary: 'Project future outcomes to test claim validity' },
  { id: 'SL-9', summary: 'Track claim evolution under pressure and contradiction' },
  { id: 'SL-10', summary: 'Map distortion in closed information loops' },
  { id: 'SL-11', summary: 'Evaluate technocratic and algorithmic governance claims' },
  { id: 'SL-12', summary: 'Assess digital infrastructure control and dependencies' },
];

// ---- Module Selector ------------------------------------------------------

function buildSelectorPrompt(
  narrative: NarrativeInput,
  context: AnalysisContext,
  stats: SignalStats | null,
): string {
  const lines: string[] = [
    'You are selecting analytical modules for a media narrative analysis.',
    '',
    `NARRATIVE: ${narrative.label}`,
  ];
  if (narrative.moral_frame) lines.push(`MORAL FRAME: ${narrative.moral_frame}`);
  lines.push(
    `EVENT: ${context.event_title || 'N/A'}  |  REGION: ${context.centroid_name || 'N/A'}  |  TRACK: ${context.track || 'N/A'}`,
    `ENTITY TYPE: ${context.entity_type}`,
  );

  if (stats) {
    lines.push('', 'COVERAGE DATA:');
    lines.push(`- Publishers: ${stats.publisher_count}, concentration (HHI): ${stats.publisher_hhi.toFixed(3)}`);
    // Language distribution: top 3
    const langEntries = Object.entries(stats.language_distribution)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([lang, count]) => `${lang} ${count}`)
      .join(', ');
    lines.push(`- Languages: ${stats.language_count} (${langEntries})`);
    // Geographic focus: top 5 countries
    const geoEntries = Object.entries(stats.entity_country_distribution || {})
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([cc, count]) => `${cc} (${count})`)
      .join(', ');
    if (geoEntries) lines.push(`- Geographic focus: ${geoEntries}`);
    // Key actors
    const actorNames = (stats.top_actors || []).slice(0, 5).map((a) => a.name).join(', ');
    if (actorNames) lines.push(`- Key actors: ${actorNames}`);
    lines.push(`- Date span: ${stats.date_range_days} days`);
  }

  lines.push(
    '',
    '3 core modules are already included (CL-0, NL-3, SL-8).',
    'Select exactly 3 additional modules from the list below.',
    '',
    'AVAILABLE MODULES:',
  );
  for (const entry of MODULE_CATALOG) {
    lines.push(`${entry.id}: ${entry.summary}`);
  }

  lines.push(
    '',
    'Respond with exactly 3 module IDs and a brief rationale, one per line:',
    'FL-3: [rationale]',
    'NL-1: [rationale]',
    'SL-1: [rationale]',
  );

  return lines.join('\n');
}

export async function selectModules(
  narrative: NarrativeInput,
  context: AnalysisContext,
  stats: SignalStats | null,
): Promise<string[]> {
  const SELECTOR_TIMEOUT_MS = 15_000;

  try {
    if (!DEEPSEEK_API_KEY) {
      console.log('[RAI selector] No API key, using fallback modules');
      return FALLBACK_MODULE_IDS;
    }

    const prompt = buildSelectorPrompt(narrative, context, stats);

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), SELECTOR_TIMEOUT_MS);

    let raw: string;
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
          temperature: 0,
          max_tokens: 200,
        }),
        signal: controller.signal,
      });

      if (!res.ok) {
        const text = await res.text();
        console.error(`[RAI selector] API error ${res.status}: ${text.slice(0, 200)}`);
        return FALLBACK_MODULE_IDS;
      }

      const data = await res.json();
      raw = data.choices?.[0]?.message?.content || '';
    } finally {
      clearTimeout(timeout);
    }

    if (!raw) {
      console.log('[RAI selector] Empty response, using fallback');
      return FALLBACK_MODULE_IDS;
    }

    console.log('[RAI selector] Response:', raw);

    // Extract module IDs from response
    const validIds = new Set(MODULE_CATALOG.map((e) => e.id));
    const matches = raw.match(/(CL-\d+|FL-\d+|NL-\d+|SL-\d+)/g) || [];
    const selected: string[] = [];
    for (const id of matches) {
      if (validIds.has(id) && !selected.includes(id)) {
        selected.push(id);
        if (selected.length === 3) break;
      }
    }

    if (selected.length < 3) {
      console.log(`[RAI selector] Only ${selected.length} valid IDs found, padding with fallback`);
      for (const fb of FALLBACK_MODULE_IDS) {
        if (!selected.includes(fb)) {
          selected.push(fb);
          if (selected.length === 3) break;
        }
      }
    }

    console.log('[RAI selector] Selected modules:', selected.join(', '));
    return selected;
  } catch (err) {
    console.error('[RAI selector] Error:', err);
    return FALLBACK_MODULE_IDS;
  }
}

// ---- Prompt Builder -------------------------------------------------------

function formatModulesForPrompt(modules: RaiModule[]): string {
  const moduleIds = modules.map((m) => m.id);
  const lines: string[] = [
    '**SELECTED RAI ANALYSIS COMPONENTS:**',
    '',
    `**Execution Order:** ${moduleIds.join(' -> ')}`,
    '',
  ];

  for (const mod of modules) {
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
    '- Use `## ` (h2) for each module heading (e.g., ## CL-0: Narrative Contextualization)',
    '- Use bullet lists for findings and blind spots',
    '- Keep each section to 2-4 paragraphs max',
    '- Mark philosophical insights with `> ` blockquote syntax',
    '- Use `### ` (h3) for sub-sections within a module if needed',
    '',
  );

  // 8. Premise citation instruction
  parts.push(
    'When referencing RAI premises (D1.1, D2.5, etc.), always explain what the premise says inline rather than just citing the ID. The reader does not have access to the premise library.',
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
export { CORE_MODULE_IDS };
