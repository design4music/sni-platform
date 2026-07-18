const pptxgen = require("pptxgenjs");

let pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.author = "RY";
pres.title = "RY Check";

const W = 13.33, H = 7.5;
const BLACK = "1A1A1A";
const MUTE = "8A8A8A";
const ACCENT = "1C3F91"; // deep blue accent, used sparingly
const BG = "FFFFFF";

function baseSlide() {
  const s = pres.addSlide();
  s.background = { color: BG };
  return s;
}

function centerText(s, runs, opts) {
  s.addText(runs, Object.assign({
    x: 0, y: 0, w: W, h: H,
    align: "center", valign: "middle",
    fontFace: "Calibri", color: BLACK,
    margin: 0
  }, opts));
}

// Slide 1 - Title
{
  const s = baseSlide();
  centerText(s, [
    { text: "RY Check", options: { fontSize: 64, bold: true, breakLine: true, color: BLACK } },
    { text: "Highlight anything. Know if you can trust it.", options: { fontSize: 22, color: MUTE, breakLine: true } },
  ], { y: -0.4 });
  s.addText("Hamburg Startup Night", {
    x: 0, y: H - 1.0, w: W, h: 0.5, align: "center", valign: "middle",
    fontFace: "Calibri", fontSize: 14, color: MUTE, margin: 0
  });
}

// Slide 2 - Problem
{
  const s = baseSlide();
  centerText(s, [
    { text: "You read something suspicious.", options: { fontSize: 40, bold: true, breakLine: true } },
    { text: "Then what?", options: { fontSize: 40, bold: true, breakLine: true, color: ACCENT } },
  ], { y: -0.6 });
  s.addText("Today's tools answer “summarize” or “rewrite.” None answer “should I trust this.”", {
    x: 1.5, y: H - 2.0, w: W - 3, h: 0.8, align: "center", valign: "middle",
    fontFace: "Calibri", fontSize: 18, color: MUTE, margin: 0
  });
}

// Slide 3 - Insight
{
  const s = baseSlide();
  s.addText([
    { text: "WorldBrief", options: { fontSize: 28, bold: true, breakLine: true } },
    { text: "You have to go to it.", options: { fontSize: 18, color: MUTE } },
  ], { x: 0.5, y: 2.9, w: (W / 2) - 0.6, h: 1.7, align: "center", valign: "middle", fontFace: "Calibri", margin: 0 });
  s.addText([
    { text: "RY Check", options: { fontSize: 28, bold: true, breakLine: true, color: ACCENT } },
    { text: "It meets you where you already are.", options: { fontSize: 18, color: MUTE } },
  ], { x: W / 2 + 0.1, y: 2.9, w: (W / 2) - 0.6, h: 1.7, align: "center", valign: "middle", fontFace: "Calibri", margin: 0 });
}

// Slide 4 - How it works
{
  const s = baseSlide();
  centerText(s, [
    { text: "Highlight.", options: { fontSize: 34, bold: true, breakLine: true } },
    { text: "Ask, “Is this true?”", options: { fontSize: 34, bold: true, breakLine: true } },
    { text: "Get an instant read.", options: { fontSize: 34, bold: true, breakLine: true, color: ACCENT } },
  ], { lineSpacingMultiple: 1.6 });
}

// Slide 5 - Demo example
{
  const s = baseSlide();
  s.addText("“China is preparing to invade Taiwan.”", {
    x: 1, y: 1.5, w: W - 2, h: 1.0, align: "center", valign: "middle",
    fontFace: "Calibri", fontSize: 26, italic: true, color: BLACK, margin: 0
  });
  const lines = [
    "Claim type:  Prediction",
    "Evidence:  Weak",
    "Missing:  timeframe, sourcing",
    "Framing:  Escalatory",
  ];
  s.addText(lines.map((t, i) => ({
    text: t,
    options: { fontSize: 20, color: i === 1 ? ACCENT : BLACK, breakLine: i < lines.length - 1, align: "center" }
  })), {
    x: 2.5, y: 3.3, w: W - 5, h: 2.2, valign: "middle", fontFace: "Calibri", margin: 0, paraSpaceAfter: 10
  });
}

// Slide 6 - Why it spreads
{
  const s = baseSlide();
  centerText(s, [
    { text: "People already screenshot outrageous claims.", options: { fontSize: 30, bold: true, breakLine: true } },
    { text: "Now they screenshot the check.", options: { fontSize: 30, bold: true, breakLine: true, color: ACCENT } },
  ], { y: -0.4 });
  s.addText("Virality through shareable cards, not ads.", {
    x: 1.5, y: H - 1.8, w: W - 3, h: 0.7, align: "center", valign: "middle",
    fontFace: "Calibri", fontSize: 16, color: MUTE, margin: 0
  });
}

// Slide 7 - Business model
{
  const s = baseSlide();
  const cols = [
    ["Free", "Daily limit", "Quick reads"],
    ["Pro", "Unlimited", "Full reports, saved history"],
    ["Enterprise", "Journalists, researchers, teams"],
  ];
  const colW = (W - 1.6) / 3;
  cols.forEach((c, i) => {
    const x = 0.8 + i * colW;
    const runs = [{ text: c[0], options: { fontSize: 24, bold: true, color: i === 1 ? ACCENT : BLACK, breakLine: true } }];
    for (let j = 1; j < c.length; j++) {
      runs.push({ text: c[j], options: { fontSize: 15, color: MUTE, breakLine: j < c.length - 1 } });
    }
    s.addText(runs, { x, y: 2.6, w: colW - 0.3, h: 2.3, align: "center", valign: "middle", fontFace: "Calibri", margin: 0, paraSpaceAfter: 8 });
  });
}

// Slide 8 - Fit with WorldBrief
{
  const s = baseSlide();
  centerText(s, [
    { text: "WorldBrief asks what's happening in the world.", options: { fontSize: 26, breakLine: true } },
    { text: "RY Check asks: can I rely on this one thing.", options: { fontSize: 26, breakLine: true, color: ACCENT } },
  ], { y: -0.5 });
  s.addText("Same engine. Two entry points.", {
    x: 1.5, y: H - 1.9, w: W - 3, h: 0.7, align: "center", valign: "middle",
    fontFace: "Calibri", fontSize: 16, color: MUTE, margin: 0
  });
}

// Slide 9 - Close / ask
{
  const s = baseSlide();
  centerText(s, [
    { text: "RY Check", options: { fontSize: 44, bold: true, breakLine: true } },
    { text: "The reflex for information literacy.", options: { fontSize: 20, color: MUTE, breakLine: true } },
  ], { y: -0.6 });
  s.addText("Looking for early users and feedback.", {
    x: 1.5, y: H - 1.8, w: W - 3, h: 0.7, align: "center", valign: "middle",
    fontFace: "Calibri", fontSize: 16, color: ACCENT, margin: 0
  });
}

pres.writeFile({ fileName: "RY_Check_Pitch_Deck.pptx" }).then(() => console.log("done"));
