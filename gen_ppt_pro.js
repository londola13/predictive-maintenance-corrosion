const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.defineLayout({ name: "W", width: 13.333, height: 7.5 });
p.layout = "W";
// Pagination auto en bas (orange, lisible sur fond clair comme foncé)
const _add = p.addSlide.bind(p);
p.addSlide = function (o) { const sl = _add(o); sl.slideNumber = { x: 0, y: 7.08, w: 13.333, h: 0.3, fontFace: "Calibri", fontSize: 10, color: "E67E22", align: "center" }; return sl; };

const NAVY = "1A3A5C", ORANGE = "E67E22", WHITE = "FFFFFF",
      GREY = "5A6B7B", LIGHT = "EEF3F8", DARKTXT = "1F2933", ICE = "CADCFC";
const HEAD = "Georgia", BODY = "Calibri";

function tag(s, n, title) {
  if (n) s.addText(n, { x: 0.5, y: 0.4, w: 0.9, h: 0.7, fontFace: HEAD, fontSize: 22, bold: true,
    color: WHITE, fill: { color: ORANGE }, align: "center", valign: "middle", rectRadius: 0.05, shape: "roundRect" });
  s.addText(title, { x: n ? 1.55 : 0.5, y: 0.4, w: 11.2, h: 0.7, fontFace: HEAD, fontSize: 26, bold: true,
    color: NAVY, align: "left", valign: "middle" });
}
function card(s, x, y, w, h, head, body, headColor) {
  s.addShape("roundRect", { x, y, w, h, fill: { color: LIGHT }, line: { color: headColor || ORANGE, width: 1.5 }, rectRadius: 0.08 });
  s.addText(head, { x: x + 0.22, y: y + 0.18, w: w - 0.44, h: 0.5, fontFace: BODY, fontSize: 16, bold: true, color: headColor || NAVY, align: "left" });
  s.addText(body, { x: x + 0.22, y: y + 0.75, w: w - 0.44, h: h - 0.9, fontFace: BODY, fontSize: 14, color: DARKTXT, align: "left", valign: "top", lineSpacingMultiple: 1.1 });
}

// ===== S1 Garde =====
let s = p.addSlide(); s.background = { color: NAVY };
s.addShape("rect", { x: 0, y: 5.6, w: 13.333, h: 0.12, fill: { color: ORANGE } });
s.addText("Mon projet professionnel", { x: 0.8, y: 2.3, w: 11.7, h: 1.1, fontFace: HEAD, fontSize: 44, bold: true, color: WHITE });
s.addText("Où je me vois 2 à 3 ans après le Mastère Spécialisé", { x: 0.8, y: 3.4, w: 11.7, h: 0.8, fontFace: BODY, fontSize: 23, color: ORANGE });
s.addText("BATOUMBI IKOND Ricky Parfait", { x: 0.8, y: 6.4, w: 11.7, h: 0.5, fontFace: BODY, fontSize: 15, bold: true, color: WHITE });

// ===== S2 Point de depart =====
s = p.addSlide(); s.background = { color: WHITE };
tag(s, "", "Mon point de départ");
s.addText("Je ne pars pas de zéro — je pars d'une expertise terrain que je veux faire passer à l'échelle.",
  { x: 0.7, y: 1.5, w: 12, h: 0.9, fontFace: HEAD, fontSize: 20, italic: true, color: NAVY, lineSpacingMultiple: 1.1 });
const dep = [["5 ans d'expérience", "Maintenance, automatisme, dev — sur infrastructure critique"], ["Profil IT/OT", "Le pont entre les opérations industrielles et la donnée"], ["Un prototype I4.0", "Conçu et réalisé de A à Z, avec des données réelles"]];
let dx = 0.7;
dep.forEach(d => {
  s.addShape("roundRect", { x: dx, y: 2.7, w: 3.95, h: 2.4, fill: { color: NAVY }, rectRadius: 0.1 });
  s.addText(d[0], { x: dx + 0.2, y: 3.0, w: 3.55, h: 0.9, fontFace: HEAD, fontSize: 19, bold: true, color: ORANGE, align: "left", valign: "top" });
  s.addText(d[1], { x: dx + 0.2, y: 3.9, w: 3.55, h: 1.1, fontFace: BODY, fontSize: 14.5, color: WHITE, align: "left", valign: "top", lineSpacingMultiple: 1.1 });
  dx += 4.15;
});
s.addText("Ce qui me manque : la dimension managériale et stratégique pour piloter ces projets à grande échelle.",
  { x: 0.7, y: 5.5, w: 12, h: 0.8, fontFace: BODY, fontSize: 16, color: GREY });

// ===== S3 Introspection =====
s = p.addSlide(); s.background = { color: WHITE };
tag(s, "1", "Introspection");
card(s, 0.7, 1.7, 5.9, 4.7, "✓  Ce que je veux faire",
  "• Concevoir et PILOTER des projets d'innovation industrielle\n\n• Avoir un impact concret et mesurable\n\n• Être à l'interface entre la technique, les opérations et la décision\n\n• Construire, transformer une organisation", NAVY);
card(s, 6.8, 1.7, 5.8, 4.7, "✕  Ce que je ne veux plus faire",
  "• Rester un simple exécutant\n\n• Subir la maintenance réactive, courir après les pannes\n\n• Être un ingénieur interchangeable parmi d'autres\n\n• Travailler sans voir l'impact de ce que je produis", ORANGE);

// ===== S4 Motivation =====
s = p.addSlide(); s.background = { color: WHITE };
tag(s, "2", "Ce qui me motive");
const mot = [
  ["Impact", "Voir une solution que j'ai conçue changer concrètement la réalité d'une usine."],
  ["Construire", "Ma nature de bâtisseur : partir d'un problème réel et en faire une solution qui tourne."],
  ["Autonomie", "Porter la responsabilité d'un projet, décider, piloter — pas seulement exécuter."],
  ["Être rare & utile", "Un profil I4.0 capable de toute la chaîne, là où ces compétences sont rares."]
];
let mx = 0.7, my = 1.7;
mot.forEach((m, i) => {
  const x = 0.7 + (i % 2) * 6.1, y = 1.7 + Math.floor(i / 2) * 2.4;
  s.addShape("roundRect", { x, y, w: 5.8, h: 2.15, fill: { color: LIGHT }, line: { color: i % 2 ? ORANGE : NAVY, width: 1.5 }, rectRadius: 0.08 });
  s.addText(m[0], { x: x + 0.25, y: y + 0.2, w: 5.3, h: 0.6, fontFace: HEAD, fontSize: 19, bold: true, color: i % 2 ? ORANGE : NAVY });
  s.addText(m[1], { x: x + 0.25, y: y + 0.85, w: 5.3, h: 1.1, fontFace: BODY, fontSize: 14.5, color: DARKTXT, lineSpacingMultiple: 1.1 });
});
s.addText("La stabilité financière viendra comme conséquence — pas comme moteur principal.",
  { x: 0.7, y: 6.55, w: 12, h: 0.5, fontFace: BODY, fontSize: 13, italic: true, color: GREY });

// ===== S5 CV futur (central) =====
s = p.addSlide(); s.background = { color: WHITE };
tag(s, "3", "Mon CV futur — vers 2030");
// bandeau identite
s.addShape("roundRect", { x: 0.7, y: 1.6, w: 11.9, h: 1.15, fill: { color: NAVY }, rectRadius: 0.08 });
s.addText("BATOUMBI IKOND Ricky Parfait", { x: 1.0, y: 1.72, w: 7.5, h: 0.5, fontFace: HEAD, fontSize: 20, bold: true, color: WHITE });
s.addText("Chef de projet / Référent Transformation Industrie 4.0", { x: 1.0, y: 2.2, w: 8.5, h: 0.45, fontFace: BODY, fontSize: 16, color: ORANGE });
s.addText("Grand groupe industriel\n(énergie / oil & gas)", { x: 9.7, y: 1.72, w: 2.7, h: 0.9, fontFace: BODY, fontSize: 13, color: ICE, align: "right", valign: "middle" });
// colonnes missions / acquis
card(s, 0.7, 2.95, 5.9, 3.5, "Mes missions",
  "• Déployer des solutions de maintenance prédictive sur des équipements critiques\n\n• Piloter des projets IT/OT : du capteur à la décision\n\n• Mener la conduite du changement auprès des équipes terrain", NAVY);
card(s, 6.8, 2.95, 5.8, 3.5, "Mes nouvelles compétences (acquises au MS)",
  "• Construire un business case et défendre un budget\n\n• Méthode de gestion de projet d'innovation\n\n• Conduite du changement & management d'équipe\n\n• Vision stratégique de la transformation", ORANGE);

// ===== S6 Projets / trajectoire =====
s = p.addSlide(); s.background = { color: WHITE };
tag(s, "4", "Mes projets — une trajectoire en 2 temps");
s.addShape("roundRect", { x: 0.7, y: 1.8, w: 5.9, h: 3.6, fill: { color: LIGHT }, line: { color: NAVY, width: 1.5 }, rectRadius: 0.08 });
s.addText("TEMPS 1", { x: 0.95, y: 2.0, w: 5.4, h: 0.5, fontFace: HEAD, fontSize: 18, bold: true, color: NAVY });
s.addText("Salarié en grand groupe", { x: 0.95, y: 2.5, w: 5.4, h: 0.5, fontFace: BODY, fontSize: 16, bold: true, color: ORANGE });
s.addText("Acquérir l'échelle, le réseau et l'expérience de projets d'envergure. On ne conseille bien que ce qu'on a soi-même piloté.",
  { x: 0.95, y: 3.05, w: 5.4, h: 2.1, fontFace: BODY, fontSize: 14.5, color: DARKTXT, valign: "top", lineSpacingMultiple: 1.15 });
s.addText("➜", { x: 6.55, y: 3.0, w: 0.7, h: 1.0, fontSize: 34, bold: true, color: GREY, align: "center", valign: "middle" });
s.addShape("roundRect", { x: 7.2, y: 1.8, w: 5.4, h: 3.6, fill: { color: NAVY }, rectRadius: 0.08 });
s.addText("TEMPS 2", { x: 7.45, y: 2.0, w: 4.9, h: 0.5, fontFace: HEAD, fontSize: 18, bold: true, color: ICE });
s.addText("Conseil indépendant", { x: 7.45, y: 2.5, w: 4.9, h: 0.5, fontFace: BODY, fontSize: 16, bold: true, color: ORANGE });
s.addText("Créer mon activité de conseil en transformation I4.0 pour les industriels d'Afrique centrale — un marché à fort potentiel et peu de concurrents.",
  { x: 7.45, y: 3.05, w: 4.9, h: 2.1, fontFace: BODY, fontSize: 14.5, color: WHITE, valign: "top", lineSpacingMultiple: 1.15 });
s.addText("Mon ancrage : l'Afrique centrale, où les industriels accumulent des décennies de données inexploitées.",
  { x: 0.7, y: 5.7, w: 12, h: 0.7, fontFace: HEAD, fontSize: 16, italic: true, bold: true, color: NAVY });

// ===== S7 Ambitions timeline =====
s = p.addSlide(); s.background = { color: WHITE };
tag(s, "5", "Mes ambitions");
const amb = [["COURT TERME", "À la sortie du MS", "Intégrer un grand groupe comme chef de projet / référent Industrie 4.0.", ORANGE],
  ["MOYEN TERME", "3 à 5 ans", "Référent confirmé : plusieurs déploiements réussis, un réseau industriel solide.", NAVY],
  ["LONG TERME", "5 à 10 ans", "Créer et diriger mon activité de conseil en transformation I4.0 pour l'Afrique.", ORANGE]];
let ax = 0.7;
amb.forEach(a => {
  s.addShape("roundRect", { x: ax, y: 2.0, w: 3.95, h: 4.0, fill: { color: LIGHT }, line: { color: a[3], width: 2 }, rectRadius: 0.1 });
  s.addText(a[0], { x: ax + 0.2, y: 2.25, w: 3.55, h: 0.6, fontFace: HEAD, fontSize: 18, bold: true, color: a[3], align: "center" });
  s.addText(a[1], { x: ax + 0.2, y: 2.95, w: 3.55, h: 0.5, fontFace: BODY, fontSize: 14, italic: true, color: GREY, align: "center" });
  s.addText(a[2], { x: ax + 0.2, y: 3.7, w: 3.55, h: 2.1, fontFace: BODY, fontSize: 15, color: DARKTXT, align: "center", valign: "top", lineSpacingMultiple: 1.15 });
  ax += 4.15;
});

// ===== S8 Pourquoi ce MS =====
s = p.addSlide(); s.background = { color: WHITE };
tag(s, "", "Pourquoi ce Mastère est mon chaînon manquant");
card(s, 0.7, 1.7, 5.9, 3.0, "Ce que j'ai déjà", "L'expertise technique de l'Industrie 4.0 : je sais CONCEVOIR un système, du capteur à l'IA. Je l'ai prouvé.", NAVY);
card(s, 6.8, 1.7, 5.8, 3.0, "Ce que le MS m'apporte", "Le langage business, la méthode de gestion de projet d'innovation, la conduite du changement, le réseau et la légitimité.", ORANGE);
s.addText("« Sans ce Mastère, je reste un excellent technicien. Avec lui, je deviens un chef de projet capable de transformer une organisation. »",
  { x: 0.7, y: 5.1, w: 12, h: 1.2, fontFace: HEAD, fontSize: 19, italic: true, bold: true, color: NAVY, align: "center", lineSpacingMultiple: 1.15 });

// ===== S9 Conclusion =====
s = p.addSlide(); s.background = { color: NAVY };
s.addShape("rect", { x: 0, y: 1.7, w: 13.333, h: 0.1, fill: { color: ORANGE } });
s.addText("Mon projet, en une phrase", { x: 0.8, y: 2.1, w: 11.7, h: 0.7, fontFace: BODY, fontSize: 20, color: ORANGE });
s.addText("Faire passer l'expertise Industrie 4.0 du terrain à la stratégie — et l'ancrer là où elle a le plus de valeur.",
  { x: 0.8, y: 2.9, w: 11.7, h: 1.6, fontFace: HEAD, fontSize: 30, bold: true, color: WHITE, lineSpacingMultiple: 1.1 });
s.addText("Merci.", { x: 0.8, y: 5.7, w: 11.7, h: 0.6, fontFace: HEAD, fontSize: 24, bold: true, color: WHITE });

p.writeFile({ fileName: "C:/Users/BATOUMBI IKOND RICKY/Documents/Entretien_Projet_Professionnel.pptx" })
  .then(f => console.log("PPTX CREE:", f))
  .catch(e => { console.error("ERREUR:", e); process.exit(1); });
