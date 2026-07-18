const pptxgen = require("pptxgenjs");

let pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.author = "RY";
pres.title = "Reality Check";

const W = 13.33, H = 7.5;
const BLACK = "1A1A1A";
const MUTE = "8A8A8A";
const ACCENT = "1C3F91";
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

function footer(s, text, color) {
  s.addText(text, {
    x: 1.5, y: H - 1.9, w: W - 3, h: 0.7, align: "center", valign: "middle",
    fontFace: "Calibri", fontSize: 16, color: color || MUTE, margin: 0
  });
}

// 1. Title
{
  const s = baseSlide();
  centerText(s, [
    { text: "Reality Check", options: { fontSize: 60, bold: true, breakLine: true } },
    { text: "A reasoning helper for polarized debates.", options: { fontSize: 22, color: MUTE, breakLine: true } },
  ], { y: -0.4 });
  s.addText("Hamburg Startup Night", {
    x: 0, y: H - 1.0, w: W, h: 0.5, align: "center", valign: "middle",
    fontFace: "Calibri", fontSize: 14, color: MUTE, margin: 0
  });
}

// 2. The story
{
  const s = baseSlide();
  centerText(s, [
    { text: "Two of my friends, aligned for years.", options: { fontSize: 30, breakLine: true } },
    { text: "One COVID debate. A public split.", options: { fontSize: 30, breakLine: true, color: ACCENT } },
  ], { y: -0.7 });
  s.addText("Caitlin Johnston and Eva Bartlett — sharp, independent, critical thinkers. Still split.", {
    x: 1.2, y: H - 2.0, w: W - 2.4, h: 0.8, align: "center", valign: "middle",
    fontFace: "Calibri", fontSize: 17, color: MUTE, margin: 0
  });
}

// 3. The idea
{
  const s = baseSlide();
  centerText(s, [
    { text: "Not a fact-checker.", options: { fontSize: 34, bold: true, breakLine: true } },
    { text: "A reasoning helper.", options: { fontSize: 34, bold: true, breakLine: true, color: ACCENT } },
  ], { y: -0.6 });
  s.addText("Separate known from speculative. Surface fallacies and missing context. Build an adequate worldview together.", {
    x: 1.2, y: H - 2.2, w: W - 2.4, h: 1.0, align: "center", valign: "middle",
    fontFace: "Calibri", fontSize: 17, color: MUTE, margin: 0
  });
}

// 4. How it works
{
  const s = baseSlide();
  centerText(s, [
    { text: "Highlight text. Add your thoughts.", options: { fontSize: 30, bold: true, breakLine: true } },
    { text: "Run the analysis.", options: { fontSize: 30, bold: true, breakLine: true } },
    { text: "Get a reasoned breakdown.", options: { fontSize: 30, bold: true, breakLine: true, color: ACCENT } },
  ], { lineSpacingMultiple: 1.6, y: -0.3 });
  footer(s, "A browser extension.");
}

// 5. Under the hood
{
  const s = baseSlide();
  s.addText([
    { text: "AI-powered. ", options: { color: MUTE } },
    { text: "Framework-driven.", options: { color: ACCENT, bold: true } },
  ], { x: 0, y: 1.2, w: W, h: 0.8, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 32, bold: true, margin: 0 });
  const lines = [
    "Extract core claims",
    "Strip emotional framing",
    "Add missing context",
    "Check sources",
    "Flag bias and omissions",
  ];
  s.addText(lines.map((t, i) => ({
    text: t,
    options: { fontSize: 19, breakLine: i < lines.length - 1, align: "center" }
  })), { x: 2, y: 2.6, w: W - 4, h: 3.0, valign: "middle", fontFace: "Calibri", margin: 0, paraSpaceAfter: 8 });
  footer(s, "A coach for critical thinking.", ACCENT);
}

// 6. Status
{
  const s = baseSlide();
  centerText(s, [
    { text: "Prototype tested on ambiguous political narratives.", options: { fontSize: 24, breakLine: true } },
    { text: "Extensible to any domain.", options: { fontSize: 24, breakLine: true } },
  ], { y: -0.8 });
  s.addText("A book detailing the methodology and philosophy is in progress.", {
    x: 1.2, y: H - 1.9, w: W - 2.4, h: 0.7, align: "center", valign: "middle",
    fontFace: "Calibri", fontSize: 17, color: MUTE, margin: 0
  });
}

// 7. Business model
{
  const s = baseSlide();
  centerText(s, [
    { text: "Freemium.", options: { fontSize: 30, bold: true, breakLine: true } },
    { text: "Paid: save, share, export, more.", options: { fontSize: 22, color: MUTE, breakLine: true } },
  ], { y: -0.8 });
  s.addText("B2C, slow traction expected. Purpose: validate the concept, battle-test the framework.", {
    x: 1.2, y: H - 2.0, w: W - 2.4, h: 0.8, align: "center", valign: "middle",
    fontFace: "Calibri", fontSize: 17, color: MUTE, margin: 0
  });
}

// 8. Bigger picture
{
  const s = baseSlide();
  centerText(s, [
    { text: "WorldBrief", options: { fontSize: 40, bold: true, breakLine: true, color: ACCENT } },
    { text: "Corporate risk and geopolitical analysis.", options: { fontSize: 22, color: MUTE, breakLine: true } },
    { text: "Same reasoning engine at its core.", options: { fontSize: 22, breakLine: true } },
  ], { y: -0.5 });
  footer(s, "worldbrief.info — live 6 months.");
}

// 9. Team
{
  const s = baseSlide();
  const cols = [
    ["Founder", "Two years, solo"],
    ["Marcus Böhm", "Hamburg — business dev, corporate risk"],
    ["Dietz Tönnies", "Munich — sales and marketing, media"],
  ];
  const colW = (W - 1.6) / 3;
  cols.forEach((c, i) => {
    const x = 0.8 + i * colW;
    s.addText([
      { text: c[0], options: { fontSize: 22, bold: true, color: i === 0 ? BLACK : ACCENT, breakLine: true } },
      { text: c[1], options: { fontSize: 14, color: MUTE } },
    ], { x, y: 2.7, w: colW - 0.3, h: 2.1, align: "center", valign: "middle", fontFace: "Calibri", margin: 0, paraSpaceAfter: 8 });
  });
}

// 10. Close / status
{
  const s = baseSlide();
  s.addText("Reality Check is my excuse to stand on this stage.", {
    x: 1.0, y: 0.5, w: W - 2.0, h: 0.9, align: "center", valign: "middle",
    fontFace: "Calibri", fontSize: 24, bold: true, color: BLACK, margin: 0
  });
  const lines = [
    "Reality Check — MVP available on demand as a web app",
    "Reality Check — a pilot to validate the concept",
  ];
  s.addText(lines.map((t, i) => ({
    text: t, options: { fontSize: 16, color: MUTE, breakLine: i < lines.length - 1, align: "center" }
  })), { x: 1.2, y: 1.7, w: W - 2.4, h: 1.2, valign: "middle", fontFace: "Calibri", margin: 0, paraSpaceAfter: 6 });

  s.addText("WorldBrief.info", {
    x: 0.5, y: 3.3, w: W - 1.0, h: 1.5, align: "center", valign: "middle",
    fontFace: "Calibri", fontSize: 60, bold: true, color: ACCENT, margin: 0
  });
  s.addText("should spark your interest 😉", {
    x: 1.0, y: 4.85, w: W - 2.0, h: 0.8, align: "center", valign: "middle",
    fontFace: "Calibri", fontSize: 26, bold: true, color: ACCENT, margin: 0
  });
}

pres.writeFile({ fileName: "Reality_Check_Pitch_Deck.pptx" }).then(() => console.log("done"));
