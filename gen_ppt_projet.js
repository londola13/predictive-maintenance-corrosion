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
const IMG = "d:/Claude code/predictive-maintenance-corrosion/plots/3runs_comparaison.png";

function tag(s, n, title) {
  if (n) s.addText(n, { x: 0.5, y: 0.4, w: 0.95, h: 0.7, fontFace: HEAD, fontSize: 19, bold: true,
    color: WHITE, fill: { color: ORANGE }, align: "center", valign: "middle", rectRadius: 0.05, shape: "roundRect" });
  s.addText(title, { x: n ? 1.6 : 0.5, y: 0.4, w: 11.2, h: 0.7, fontFace: HEAD, fontSize: 25, bold: true,
    color: NAVY, align: "left", valign: "middle" });
}
function bullets(s, items, opts) {
  const o = Object.assign({ x: 0.7, y: 1.5, w: 12, h: 5.3, fontSize: 17 }, opts || {});
  s.addText(items.map(t => ({ text: t, options: { bullet: { code: "2022", indent: 18 }, color: DARKTXT, paraSpaceAfter: 12 } })),
    { x: o.x, y: o.y, w: o.w, h: o.h, fontFace: BODY, fontSize: o.fontSize, valign: "top", lineSpacingMultiple: 1.05 });
}
function card(s, x, y, w, h, head, body, headColor) {
  s.addShape("roundRect", { x, y, w, h, fill: { color: LIGHT }, line: { color: headColor || ORANGE, width: 1.5 }, rectRadius: 0.08 });
  s.addText(head, { x: x + 0.2, y: y + 0.15, w: w - 0.4, h: 0.5, fontFace: BODY, fontSize: 15, bold: true, color: headColor || NAVY, align: "left" });
  s.addText(body, { x: x + 0.2, y: y + 0.7, w: w - 0.4, h: h - 0.85, fontFace: BODY, fontSize: 13.5, color: DARKTXT, align: "left", valign: "top", lineSpacingMultiple: 1.05 });
}

// ============ S1 — Garde ============
let s = p.addSlide(); s.background = { color: NAVY };
s.addShape("rect", { x: 0, y: 5.7, w: 13.333, h: 0.12, fill: { color: ORANGE } });
s.addText("De la donnée à la décision", { x: 0.8, y: 2.2, w: 11.7, h: 1.1, fontFace: HEAD, fontSize: 44, bold: true, color: WHITE, align: "left" });
s.addText("Un système de maintenance prédictive de la corrosion", { x: 0.8, y: 3.3, w: 11.7, h: 0.8, fontFace: BODY, fontSize: 24, color: ORANGE, align: "left" });
s.addText("Projet de mémoire — Master Maintenance Industrielle & Productique", { x: 0.8, y: 6.0, w: 11.7, h: 0.5, fontFace: BODY, fontSize: 15, color: ICE, align: "left" });
s.addText("BATOUMBI IKOND Ricky Parfait", { x: 0.8, y: 6.5, w: 11.7, h: 0.5, fontFace: BODY, fontSize: 15, bold: true, color: WHITE, align: "left" });

// ============ S2 — Le projet en une phrase ============
s = p.addSlide(); s.background = { color: WHITE };
tag(s, "", "Le projet en une phrase");
s.addText("Mesurer la corrosion en temps réel, prédire la rupture, déclencher la maintenance — automatiquement.",
  { x: 0.7, y: 1.5, w: 12, h: 1.0, fontFace: HEAD, fontSize: 21, italic: true, color: NAVY, align: "left" });
const flow = [["CAPTEUR\nIoT", "Mesure la corrosion"], ["CLOUD", "Transmet & stocke"], ["IA", "Prédit la rupture"], ["GMAO", "Ordre de maintenance"]];
let fx = 0.9;
flow.forEach((f, i) => {
  s.addShape("roundRect", { x: fx, y: 3.2, w: 2.5, h: 1.7, fill: { color: i % 2 ? NAVY : ORANGE }, rectRadius: 0.1 });
  s.addText(f[0], { x: fx, y: 3.4, w: 2.5, h: 0.7, fontFace: HEAD, fontSize: 20, bold: true, color: WHITE, align: "center" });
  s.addText(f[1], { x: fx, y: 4.05, w: 2.5, h: 0.7, fontFace: BODY, fontSize: 13, color: WHITE, align: "center" });
  if (i < 3) s.addText("➜", { x: fx + 2.5, y: 3.5, w: 0.6, h: 1.0, fontSize: 28, bold: true, color: GREY, align: "center", valign: "middle" });
  fx += 3.1;
});
s.addText("Une chaîne complète, de bout en bout : du signal physique jusqu'à la décision de maintenance.",
  { x: 0.7, y: 5.4, w: 12, h: 0.6, fontFace: BODY, fontSize: 16, color: GREY, align: "center" });

// ============ S3 — Emergence de l'idee ============
s = p.addSlide(); s.background = { color: WHITE };
tag(s, "", "L'émergence de l'idée");
card(s, 0.7, 1.6, 5.9, 2.0, "Le constat terrain (COTCO)", "En planification de maintenance sur le pipeline Tchad-Cameroun, j'observe des données qui s'accumulent dans le système… sans jamais servir à anticiper les pannes.", NAVY);
card(s, 6.8, 1.6, 5.8, 2.0, "Le problème", "On RÉAGIT à la panne, on ne la PRÉDIT pas. Chaque arrêt non planifié coûte cher et met la sécurité sous tension.", ORANGE);
s.addText("Mon objectif", { x: 0.7, y: 3.9, w: 12, h: 0.5, fontFace: HEAD, fontSize: 18, bold: true, color: NAVY });
s.addText("Prouver, avec un prototype concret, qu'on peut passer du subi à l'anticipé — et rendre une industrie « intelligente » à partir de ce qu'elle possède déjà.",
  { x: 0.7, y: 4.4, w: 12, h: 1.2, fontFace: BODY, fontSize: 18, color: DARKTXT, align: "left", lineSpacingMultiple: 1.1 });

// ============ S4 — Realisation : architecture ============
s = p.addSlide(); s.background = { color: WHITE };
tag(s, "1", "La réalisation — l'architecture");
s.addText("Je conçois une chaîne où chaque brique a un rôle précis :", { x: 0.7, y: 1.45, w: 12, h: 0.5, fontFace: BODY, fontSize: 17, color: DARKTXT });
const arch = [
  ["Sonde + ESP32", "Une sonde de résistance électrique mesure la corrosion ; un microcontrôleur numérise et envoie les données."],
  ["Cloud (base de données)", "Les mesures arrivent en continu et sont stockées de façon centralisée et horodatée."],
  ["Modèle d'IA (XGBoost)", "Apprend la signature de la dégradation et prédit la vitesse de corrosion et le temps avant rupture."],
  ["Tableau de bord + GMAO", "Visualise l'état, et déclenche un ordre de maintenance dès qu'une alerte se confirme."]
];
let ay = 2.05;
arch.forEach((a, i) => {
  s.addText((i + 1).toString(), { x: 0.7, y: ay, w: 0.55, h: 0.55, fontFace: HEAD, fontSize: 18, bold: true, color: WHITE, fill: { color: NAVY }, align: "center", valign: "middle", shape: "ellipse" });
  s.addText(a[0], { x: 1.45, y: ay, w: 3.4, h: 0.55, fontFace: BODY, fontSize: 15, bold: true, color: ORANGE, align: "left", valign: "middle" });
  s.addText(a[1], { x: 4.9, y: ay - 0.05, w: 7.7, h: 0.7, fontFace: BODY, fontSize: 13.5, color: DARKTXT, align: "left", valign: "middle", lineSpacingMultiple: 1.0 });
  ay += 1.05;
});

// ============ S5 — Realisation : demarche (SANS regard metier) ============
s = p.addSlide(); s.background = { color: WHITE };
tag(s, "1", "La réalisation — ma démarche");
s.addText("Une démarche itérative, pilotée en autonomie", { x: 0.7, y: 1.45, w: 12, h: 0.5, fontFace: HEAD, fontSize: 18, bold: true, color: NAVY });
const steps = ["Concevoir", "Prototyper", "Tester en\nconditions réelles", "Entraîner\nle modèle", "Analyser\n& itérer"];
let sx = 0.8;
steps.forEach((st, i) => {
  s.addShape("roundRect", { x: sx, y: 2.2, w: 2.15, h: 1.2, fill: { color: i % 2 ? NAVY : ORANGE }, rectRadius: 0.08 });
  s.addText(st, { x: sx, y: 2.2, w: 2.15, h: 1.2, fontFace: BODY, fontSize: 14, bold: true, color: WHITE, align: "center", valign: "middle" });
  if (i < 4) s.addText("➜", { x: sx + 2.13, y: 2.3, w: 0.45, h: 1.0, fontSize: 22, bold: true, color: GREY, align: "center", valign: "middle" });
  sx += 2.5;
});
card(s, 0.7, 3.9, 5.9, 2.4, "Avec qui ?", "• Projet mené en autonomie complète\n\n• Encadrement académique : Dr Tchawe\n\n• Outils d'IA générative comme accélérateur de développement", NAVY);
card(s, 6.8, 3.9, 5.8, 2.4, "Ma méthode", "Je ne cherche pas la perfection du premier coup : je construis une version minimale qui fonctionne, je la teste sur le terrain, puis je l'améliore par boucles successives.", ORANGE);

// ============ S6 — Contexte : contraintes & risques (REFONDU) ============
s = p.addSlide(); s.background = { color: WHITE };
tag(s, "2", "Le contexte — contraintes & risques");
card(s, 0.7, 1.55, 5.9, 5.0, "⚙  Mes contraintes",
  "Des limites certaines, avec lesquelles je compose dès le départ :\n\n• Budget limité\n\n• Projet mené seul, de A à Z\n\n• Temps limité avant la soutenance\n\n• Précision extrême : détecter des variations de l'ordre du millième d'ohm", NAVY);
card(s, 6.8, 1.55, 5.8, 5.0, "⚠  Mes risques",
  "Des événements incertains qui peuvent compromettre le projet :\n\n• Sécurité : manipulation d'un acide concentré (projections, brûlures)\n\n• Perte de données : un essai dure des dizaines d'heures — une coupure (courant, Wi-Fi, capteur) peut l'anéantir\n\n• Biais expérimental caché qui fausserait les résultats", ORANGE);

// ============ S7 — La difficulte majeure : LE DEFI (navy, explicite) ============
s = p.addSlide(); s.background = { color: NAVY };
s.addText("La difficulté majeure : mesurer l'infime", { x: 0.6, y: 0.5, w: 12.1, h: 0.8, fontFace: HEAD, fontSize: 27, bold: true, color: WHITE });
s.addShape("roundRect", { x: 0.7, y: 1.5, w: 11.9, h: 1.5, fill: { color: "234A6E" }, line: { color: ORANGE, width: 1.5 }, rectRadius: 0.08 });
s.addText("Le défi", { x: 0.95, y: 1.65, w: 11.4, h: 0.4, fontFace: BODY, fontSize: 15, bold: true, color: ORANGE });
s.addText("Pour suivre la corrosion, je dois détecter des variations de résistance de l'ordre du MILLIÈME d'ohm. À cette échelle, le moindre bruit électronique noie le signal utile.",
  { x: 0.95, y: 2.05, w: 11.4, h: 0.9, fontFace: BODY, fontSize: 16, color: WHITE, valign: "top", lineSpacingMultiple: 1.1 });
s.addText("Les symptômes concrets de l'échec :", { x: 0.7, y: 3.3, w: 12, h: 0.45, fontFace: BODY, fontSize: 15, bold: true, color: ICE });
const symp = [["Capteur saturé", "Le signal devient incohérent, inexploitable."],
  ["Résultat absurde", "La résistance DIMINUE alors qu'elle devrait augmenter."],
  ["Bruit > signal", "Impossible de distinguer la vraie corrosion du bruit de mesure."]];
let px = 0.7;
symp.forEach(sy => {
  s.addShape("roundRect", { x: px, y: 3.85, w: 3.9, h: 1.7, fill: { color: "234A6E" }, line: { color: ICE, width: 1 }, rectRadius: 0.08 });
  s.addText(sy[0], { x: px + 0.2, y: 4.05, w: 3.5, h: 0.5, fontFace: HEAD, fontSize: 16, bold: true, color: ORANGE });
  s.addText(sy[1], { x: px + 0.2, y: 4.6, w: 3.5, h: 0.85, fontFace: BODY, fontSize: 13.5, color: WHITE, valign: "top", lineSpacingMultiple: 1.05 });
  px += 4.1;
});
s.addText("→ Sans mesure fiable, tout le projet s'effondre : pas de données, pas d'IA, pas de prédiction.",
  { x: 0.7, y: 5.75, w: 12, h: 0.6, fontFace: HEAD, fontSize: 16, italic: true, bold: true, color: ORANGE });

// ============ S8 — Comment je l'ai resolue (blanc) ============
s = p.addSlide(); s.background = { color: WHITE };
tag(s, "", "Comment je l'ai résolue");
const reso = [
  ["1", "Je diagnostique méthodiquement", "J'isole et je teste chaque composant un par un, je vérifie mon code ligne par ligne."],
  ["2", "Une découverte inattendue", "Mon propre multimètre de référence était défectueux et faussait mes mesures — je ne fais plus confiance aveuglément à mes instruments."],
  ["3", "Le vrai coupable", "Ce n'est pas un détail : c'est mon architecture de mesure qui est inadaptée au signal recherché."],
  ["4", "La solution", "J'abandonne ce montage pour une architecture plus simple et robuste, complétée par une calibration sur une résistance étalon connue."]
];
let ry = 1.5;
reso.forEach(r => {
  s.addText(r[0], { x: 0.7, y: ry, w: 0.55, h: 0.55, fontFace: HEAD, fontSize: 18, bold: true, color: WHITE, fill: { color: ORANGE }, align: "center", valign: "middle", shape: "ellipse" });
  s.addText(r[1], { x: 1.45, y: ry, w: 3.7, h: 0.6, fontFace: BODY, fontSize: 15, bold: true, color: NAVY, align: "left", valign: "middle" });
  s.addText(r[2], { x: 5.25, y: ry - 0.05, w: 7.3, h: 0.75, fontFace: BODY, fontSize: 13.5, color: DARKTXT, align: "left", valign: "middle", lineSpacingMultiple: 1.0 });
  ry += 0.92;
});
s.addShape("roundRect", { x: 0.7, y: 5.25, w: 11.9, h: 1.0, fill: { color: NAVY }, rectRadius: 0.08 });
s.addText([
  { text: "Résultat : ", options: { bold: true, color: ORANGE } },
  { text: "8,06 Ω mesurés pour 8,2 Ω réels — moins de 2 % d'erreur. Le dispositif fonctionne.   ", options: { color: WHITE } },
  { text: "Ma leçon : changer d'approche sans jamais lâcher l'objectif.", options: { italic: true, color: ICE } }
], { x: 0.95, y: 5.25, w: 11.4, h: 1.0, fontFace: BODY, fontSize: 14.5, valign: "middle", lineSpacingMultiple: 1.05 });

// ============ S9 — Resultat (image 3 runs) ============
s = p.addSlide(); s.background = { color: WHITE };
tag(s, "3", "Le résultat obtenu");
s.addImage({ path: IMG, x: 0.6, y: 1.5, w: 7.8, h: 4.25 });
s.addText("Démarche : 3 essais à concentrations différentes", { x: 8.6, y: 1.6, w: 4.3, h: 0.6, fontFace: BODY, fontSize: 15, bold: true, color: NAVY, valign: "top" });
s.addText([
  { text: "Faire varier l'acide produit des vitesses de corrosion différentes — indispensable pour que l'IA apprenne à généraliser.\n\n", options: { fontSize: 13, color: DARKTXT } },
  { text: "Système calibré : 8,06 Ω mesurés pour 8,2 Ω réels (< 2 % d'erreur).\n\n", options: { fontSize: 13, color: DARKTXT, bold: true } },
  { text: "Corrosion captée jusqu'à la rupture du fil. Le 3ᵉ essai est en cours en ce moment.", options: { fontSize: 13, color: ORANGE, bold: true } }
], { x: 8.6, y: 2.2, w: 4.3, h: 3.5, fontFace: BODY, valign: "top", lineSpacingMultiple: 1.05 });

// ============ S10 — Contribution personnelle ============
s = p.addSlide(); s.background = { color: WHITE };
tag(s, "3", "Ma contribution personnelle");
s.addText("J'ai conçu et réalisé l'intégralité de la chaîne, seul :", { x: 0.7, y: 1.45, w: 12, h: 0.5, fontFace: BODY, fontSize: 17, color: DARKTXT });
const contrib = [["Électronique", "conception & câblage du capteur"], ["Programmation embarquée", "firmware du microcontrôleur"], ["Cloud & données", "architecture de collecte"], ["Modèle d'IA", "features & entraînement"], ["Analyse", "interprétation des résultats"], ["Gestion de projet", "pilotage de A à Z"]];
contrib.forEach((c, i) => {
  const col = i % 3, row = Math.floor(i / 3);
  const x = 0.7 + col * 4.1, y = 2.1 + row * 1.7;
  s.addShape("roundRect", { x, y, w: 3.8, h: 1.5, fill: { color: LIGHT }, line: { color: NAVY, width: 1 }, rectRadius: 0.08 });
  s.addText(c[0], { x: x + 0.15, y: y + 0.2, w: 3.5, h: 0.5, fontFace: BODY, fontSize: 15, bold: true, color: ORANGE });
  s.addText(c[1], { x: x + 0.15, y: y + 0.7, w: 3.5, h: 0.7, fontFace: BODY, fontSize: 13, color: DARKTXT });
});
s.addText("→ Mon profil IT/OT incarné : je maîtrise toute la chaîne, du capteur physique jusqu'à la donnée exploitée.",
  { x: 0.7, y: 5.65, w: 12, h: 0.7, fontFace: HEAD, fontSize: 16, italic: true, bold: true, color: NAVY });

// ============ S11 — Innovation ============
s = p.addSlide(); s.background = { color: WHITE };
tag(s, "", "Les éléments innovants");
card(s, 0.7, 1.7, 5.9, 4.6, "Brancher l'IA sur l'existant",
  "Plutôt que tout remplacer, j'ajoute une couche d'intelligence sur l'infrastructure déjà en place.\n\n→ Un saut Industrie 3.0 → 4.0 purement logiciel : rapide, peu coûteux, peu risqué.", ORANGE);
card(s, 6.8, 1.7, 5.8, 4.6, "Une double transposabilité",
  "• En grande industrie : brancher le modèle sur des sondes déjà câblées au système de contrôle.\n\n• En PME à budget contraint : un dispositif accessible et autonome.\n\nLa même approche sert deux mondes.", NAVY);

// ============ S12 — Retour d'experience ============
s = p.addSlide(); s.background = { color: WHITE };
tag(s, "4", "Mon retour d'expérience");
card(s, 0.7, 1.7, 5.9, 4.6, "✓  Ce que j'ai acquis",
  "• Mener un projet d'innovation de A à Z, seul\n\n• La résilience face au blocage technique\n\n• Évaluer un modèle de façon critique : choisir le bon outil, pas le plus à la mode\n\n• Relier le terrain, la donnée et la décision", NAVY);
card(s, 6.8, 1.7, 5.8, 4.6, "↻  Ce que je ferais différemment",
  "• Répéter des essais en conditions IDENTIQUES (n ≥ 5) plutôt que varier : c'est la clé d'une prédiction fiable\n\n• Fixer la géométrie expérimentale dès le départ\n\n• Choisir le modèle selon le problème : physique simple ici, IA à l'échelle industrielle", ORANGE);

// ============ S13 — Conclusion ============
s = p.addSlide(); s.background = { color: NAVY };
s.addShape("rect", { x: 0, y: 1.7, w: 13.333, h: 0.1, fill: { color: ORANGE } });
s.addText("Ce prototype est la preuve concrète de ma vision", { x: 0.8, y: 2.1, w: 11.7, h: 1.0, fontFace: HEAD, fontSize: 30, bold: true, color: WHITE });
s.addText("Rendre l'industrie intelligente avec ce qu'elle possède déjà.", { x: 0.8, y: 3.2, w: 11.7, h: 0.7, fontFace: BODY, fontSize: 20, color: ORANGE });
s.addText("C'est exactement ce que je veux faire à grande échelle — et c'est pourquoi je candidate à ce Mastère Spécialisé.",
  { x: 0.8, y: 4.3, w: 11.7, h: 1.0, fontFace: BODY, fontSize: 18, color: ICE, lineSpacingMultiple: 1.1 });
s.addText("Merci.", { x: 0.8, y: 5.8, w: 11.7, h: 0.6, fontFace: HEAD, fontSize: 22, bold: true, color: WHITE });

p.writeFile({ fileName: "C:/Users/BATOUMBI IKOND RICKY/Documents/Entretien_Projet_Realise.pptx" })
  .then(f => console.log("PPTX CREE:", f))
  .catch(e => { console.error("ERREUR:", e); process.exit(1); });
