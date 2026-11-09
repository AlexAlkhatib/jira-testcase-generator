#!/usr/bin/env python3
"""Generate the technical documentation PDF for Jira Test Case Generator 2.0.0.

Requirements: reportlab, pillow
Usage: python generate_documentation.py
"""
from __future__ import annotations

import os
from datetime import date

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether,
                                NextPageTemplate, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(HERE, "Jira-Test-Case-Generator-Documentation.pdf")
IMAGES = os.path.join(HERE, "images")

NAVY = colors.HexColor("#0B1120")
NAVY_DEEP = colors.HexColor("#070B16")
VIOLET = colors.HexColor("#8B5CF6")
VIOLET_L = colors.HexColor("#C4B5FD")
INDIGO = colors.HexColor("#6366F1")
CYAN = colors.HexColor("#22D3EE")
EMERALD = colors.HexColor("#10B981")
AMBER = colors.HexColor("#F59E0B")
ROSE = colors.HexColor("#F43F5E")
INK = colors.HexColor("#1E293B")
MUTED = colors.HexColor("#64748B")
LINE = colors.HexColor("#DCE3EF")
SOFT = colors.HexColor("#F4F7FC")
WHITE = colors.white

# --------------------------------------------------------------------------
# Fonts: DejaVu when available (better accents), Helvetica fallback.
# --------------------------------------------------------------------------
FONT = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_ITALIC = "Helvetica-Oblique"
FONT_MONO = "Courier"
FONT_MONO_BOLD = "Courier-Bold"

DEJAVU_DIRS = ["/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/dejavu"]
for directory in DEJAVU_DIRS:
    regular = os.path.join(directory, "DejaVuSans.ttf")
    bold = os.path.join(directory, "DejaVuSans-Bold.ttf")
    oblique = os.path.join(directory, "DejaVuSans-Oblique.ttf")
    mono = os.path.join(directory, "DejaVuSansMono.ttf")
    mono_bold = os.path.join(directory, "DejaVuSansMono-Bold.ttf")
    if os.path.exists(regular) and os.path.exists(bold):
        pdfmetrics.registerFont(TTFont("Doc", regular))
        pdfmetrics.registerFont(TTFont("Doc-Bold", bold))
        pdfmetrics.registerFont(TTFont("Doc-Italic", oblique if os.path.exists(oblique) else regular))
        pdfmetrics.registerFont(TTFont("Doc-Mono", mono if os.path.exists(mono) else regular))
        pdfmetrics.registerFont(TTFont("Doc-Mono-Bold", mono_bold if os.path.exists(mono_bold) else bold))
        FONT, FONT_BOLD, FONT_ITALIC = "Doc", "Doc-Bold", "Doc-Italic"
        FONT_MONO, FONT_MONO_BOLD = "Doc-Mono", "Doc-Mono-Bold"
        break

styles = getSampleStyleSheet()


def style(name, **kwargs):
    base = dict(fontName=FONT, fontSize=9.4, leading=13.8, textColor=INK, alignment=TA_JUSTIFY)
    base.update(kwargs)
    return ParagraphStyle(name, **base)


S = {
    "title": style("title", fontName=FONT_BOLD, fontSize=31, leading=36, textColor=WHITE, alignment=TA_LEFT),
    "subtitle": style("subtitle", fontSize=13, leading=19, textColor=colors.HexColor("#C7D2FE"), alignment=TA_LEFT),
    "h1": style("H1", fontName=FONT_BOLD, fontSize=19, leading=23, textColor=NAVY, spaceBefore=4, spaceAfter=4, alignment=TA_LEFT),
    "h2": style("H2", fontName=FONT_BOLD, fontSize=12.5, leading=16, textColor=VIOLET, spaceBefore=10, spaceAfter=4, alignment=TA_LEFT),
    "h3": style("H3", fontName=FONT_BOLD, fontSize=10, leading=13, textColor=NAVY, spaceBefore=6, spaceAfter=2, alignment=TA_LEFT),
    "body": style("Body"),
    "body_left": style("BodyLeft", alignment=TA_LEFT),
    "small": style("Small", fontSize=8.2, leading=11.5, textColor=MUTED, alignment=TA_LEFT),
    "caption": style("Caption", fontSize=8, leading=11, textColor=MUTED, alignment=TA_CENTER, spaceBefore=5),
    "bullet": style("Bullet", leftIndent=12, bulletIndent=2, spaceAfter=2),
    "code": style("Code", fontName=FONT_MONO, fontSize=7.6, leading=10.4, textColor=colors.HexColor("#E2E8F0"), alignment=TA_LEFT),
    "toctitle": style("TOCTitle", fontName=FONT_BOLD, fontSize=19, leading=23, textColor=NAVY, alignment=TA_LEFT),
    "toc1": style("TOC1", fontName=FONT_BOLD, fontSize=9.4, leading=12.4, textColor=NAVY, alignment=TA_LEFT),
    "toc2": style("TOC2", fontSize=8.4, leading=10.6, textColor=MUTED, leftIndent=14, alignment=TA_LEFT),
}

WIDTH, HEIGHT = A4
MARGIN = 20 * mm
CONTENT_WIDTH = WIDTH - 2 * MARGIN


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def p(text, s="body"):
    return Paragraph(text, S[s])


def bullets(items, s="bullet"):
    return [Paragraph(f"•&nbsp;&nbsp;{item}", S[s]) for item in items]


def h1(text):
    return [Spacer(1, 6), Paragraph(text, S["h1"]), Spacer(1, 3),
            Table([[""]], colWidths=[CONTENT_WIDTH], rowHeights=[1.6],
                  style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), VIOLET),
                                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0)])),
            Spacer(1, 10)]


def h2(text):
    return Paragraph(text, S["h2"])


def table(data, widths, header=True, font_size=8.2, padding=5, align_left=True):
    prepared = []
    for r, row in enumerate(data):
        prepared.append([
            Paragraph(str(cell),
                      ParagraphStyle(f"cell{r}{c}", fontName=FONT_BOLD if (header and r == 0) else FONT,
                                     fontSize=font_size, leading=font_size + 2.6,
                                     textColor=WHITE if (header and r == 0) else INK,
                                     alignment=TA_LEFT)) for c, cell in enumerate(row)
        ])
    tbl = Table(prepared, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), padding),
        ("RIGHTPADDING", (0, 0), (-1, -1), padding),
        ("TOPPADDING", (0, 0), (-1, -1), padding),
        ("BOTTOMPADDING", (0, 0), (-1, -1), padding),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
    ]
    if header:
        commands += [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), WHITE)]
        for i in range(1, len(data)):
            if i % 2 == 0:
                commands.append(("BACKGROUND", (0, i), (-1, i), SOFT))
    else:
        commands.append(("BACKGROUND", (0, 0), (-1, -1), SOFT))
    tbl.setStyle(TableStyle(commands))
    return tbl


def code_block(text, width=CONTENT_WIDTH):
    inner = Paragraph(text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                      .replace(" ", "&nbsp;").replace("\n", "<br/>"), S["code"])
    tbl = Table([[inner]], colWidths=[width], hAlign="LEFT")
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0F172A")),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LINEBEFORE", (0, 0), (0, -1), 2.4, CYAN),
    ]))
    return tbl


def callout(title, text, color=VIOLET, background=colors.HexColor("#F5F3FF")):
    inner = [Paragraph(title, ParagraphStyle("ct", fontName=FONT_BOLD, fontSize=9.6, leading=12.5, textColor=color)),
             Spacer(1, 3),
             Paragraph(text, ParagraphStyle("cb", fontName=FONT, fontSize=8.6, leading=12.4, textColor=INK))]
    tbl = Table([[inner]], colWidths=[CONTENT_WIDTH])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), background),
        ("LINEBEFORE", (0, 0), (0, -1), 3, color),
        ("LEFTPADDING", (0, 0), (-1, -1), 11),
        ("RIGHTPADDING", (0, 0), (-1, -1), 11),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    return tbl


def picture(name, width=CONTENT_WIDTH, caption=None):
    path = os.path.join(IMAGES, name)
    if not os.path.exists(path):
        return Spacer(1, 1)
    from PIL import Image as PILImage
    with PILImage.open(path) as img:
        ratio = img.height / img.width
    max_height = 150 * mm
    height = width * ratio
    if height > max_height:
        width = max_height / ratio
        height = max_height
    nodes = [Spacer(1, 4), Image(path, width=width, height=height), Spacer(1, 2)]
    if caption:
        nodes.append(Paragraph(caption, S["caption"]))
    return KeepTogether(nodes)


def architect_drawing():
    d = Drawing(CONTENT_WIDTH, 132)
    boxes = [
        (4, 78, 78, 40, "Client", "Navigateur / curl", CYAN),
        (96, 78, 92, 40, "API REST", "TestCaseController", VIOLET),
        (202, 78, 100, 40, "Orchestration", "TestSuiteService", INDIGO),
        (4, 18, 118, 40, "Jira REST v3/v2", "JiraRestClient + ADF", AMBER),
        (138, 18, 100, 40, "Ollama local", "ChatClient + parsing JSON", EMERALD),
        (254, 18, 72, 40, "Réponse", "JSON / RFC 7807", MUTED),
    ]
    for (x, y, w, h, title, subtitle, color) in boxes:
        d.add(Rect(x, y, w, h, rx=5, ry=5, fillColor=colors.HexColor("#F8FAFF"),
                   strokeColor=color, strokeWidth=1.1))
        d.add(Rect(x, y, 3.2, h, rx=1, ry=1, fillColor=color, strokeColor=None))
        d.add(String(x + 10, y + h - 15, title, fontName=FONT_BOLD, fontSize=7.8, fillColor=NAVY))
        d.add(String(x + 10, y + h - 28, subtitle, fontName=FONT, fontSize=6.5, fillColor=MUTED))

    def arrow(x1, y1, x2, y2):
        d.add(Line(x1, y1, x2, y2, strokeColor=colors.HexColor("#94A3B8"), strokeWidth=1))
        d.add(Polygon([x2, y2, x2 - 4, y2 + 2.4, x2 - 4, y2 - 2.4], fillColor=colors.HexColor("#94A3B8"),
                      strokeColor=None))

    arrow(82, 98, 96, 98)
    arrow(188, 98, 202, 98)
    arrow(252, 78, 252, 58)
    arrow(63, 78, 63, 58)
    d.add(Line(252, 38, 302, 38, strokeColor=colors.HexColor("#94A3B8"), strokeWidth=1, strokeDashArray=[2, 2]))
    arrow(296, 38, 302, 38)
    d.add(String(4, 124, "Flux applicatif : de la story Jira au contrat JSON", fontName=FONT_BOLD,
                 fontSize=7.4, fillColor=MUTED))
    return d


# --------------------------------------------------------------------------
# Page decoration
# --------------------------------------------------------------------------
def draw_cover(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY_DEEP)
    canvas.rect(0, 0, WIDTH, HEIGHT, fill=1, stroke=0)
    # gradient band
    steps = 60
    for i in range(steps):
        ratio = i / steps
        color = colors.Color(
            0.043 + (0.55 - 0.043) * ratio,
            0.067 + (0.36 - 0.067) * ratio,
            0.129 + (0.97 - 0.129) * ratio,
            alpha=0.22)
        canvas.setFillColor(color)
        canvas.rect(0, HEIGHT - 90 - i * 3.2, WIDTH, 3.4, fill=1, stroke=0)
    canvas.setFillColor(VIOLET)
    canvas.circle(WIDTH - 34 * mm, HEIGHT - 42 * mm, 30 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#4C1D95"))
    canvas.circle(WIDTH - 22 * mm, HEIGHT - 55 * mm, 16 * mm, fill=1, stroke=0)
    canvas.setFillColor(CYAN)
    canvas.circle(WIDTH - 32 * mm, 26 * mm, 6 * mm, fill=1, stroke=0)

    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.setFont(FONT_BOLD, 7.6)
    canvas.drawString(MARGIN, 133 * mm, "POINTS CLÉS")
    badges = [("IA 100 % locale", CYAN), ("37 tests automatisés", EMERALD), ("API typée", VIOLET_L)]
    badge_x = MARGIN
    for label, color in badges:
        width = 44 * mm if "locale" in label else 48 * mm
        canvas.setFillColor(colors.HexColor("#111A2C"))
        canvas.setStrokeColor(color)
        canvas.setLineWidth(0.7)
        canvas.roundRect(badge_x, 112 * mm, width, 11 * mm, 3 * mm, fill=1, stroke=1)
        canvas.setFillColor(color)
        canvas.setFont(FONT_BOLD, 8)
        canvas.drawCentredString(badge_x + width / 2, 116 * mm, label)
        badge_x += width + 5 * mm

    canvas.setFillColor(colors.HexColor("#A5B4FC"))
    canvas.setFont(FONT_BOLD, 9)
    canvas.drawString(MARGIN, HEIGHT - 34 * mm, "DOCUMENTATION TECHNIQUE  ·  VERSION 2.0.0")
    canvas.setFillColor(WHITE)
    canvas.setFont(FONT_BOLD, 33)
    canvas.drawString(MARGIN, HEIGHT - 56 * mm, "Jira Test Case")
    canvas.drawString(MARGIN, HEIGHT - 69 * mm, "Generator")
    canvas.setFillColor(colors.HexColor("#C7D2FE"))
    canvas.setFont(FONT, 13)
    canvas.drawString(MARGIN, HEIGHT - 82 * mm, "Des critères d'acceptation aux cas de test, par IA locale.")

    canvas.setStrokeColor(colors.HexColor("#334155"))
    canvas.setLineWidth(0.8)
    canvas.line(MARGIN, HEIGHT - 96 * mm, WIDTH - MARGIN, HEIGHT - 96 * mm)

    canvas.setFillColor(colors.HexColor("#94A3B8"))
    canvas.setFont(FONT, 8.6)
    canvas.drawString(MARGIN, HEIGHT - 104 * mm, "Architecture  ·  API REST  ·  Sécurité  ·  Tests  ·  Exploitation")

    meta = [
        ("Auteur", "Alex Alkhatib"),
        ("Stack", "Java 17 · Spring Boot 3.5.16 · Spring AI 1.1.8"),
        ("Modèle", "Ollama (local, mistral par défaut)"),
        ("Date", "9 novembre 2026"),
        ("Licence", "MIT"),
    ]
    y = 82 * mm
    for label, value in meta:
        canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.setFont(FONT_BOLD, 8)
        canvas.drawString(MARGIN, y, label.upper())
        canvas.setFillColor(colors.HexColor("#E2E8F0"))
        canvas.setFont(FONT, 9)
        canvas.drawString(MARGIN + 26 * mm, y, value)
        y -= 8 * mm

    canvas.setFillColor(colors.HexColor("#475569"))
    canvas.setFont(FONT, 7.6)
    canvas.drawString(MARGIN, 16 * mm, "Projet personnel — QA Engineering & GenAI · Document généré automatiquement")
    canvas.restoreState()


def draw_content(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#F8FAFC"))
    canvas.rect(0, 0, WIDTH, 14 * mm, fill=1, stroke=0)
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.6)
    canvas.line(MARGIN, 14 * mm, WIDTH - MARGIN, 14 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont(FONT, 7.4)
    canvas.drawString(MARGIN, 8.6 * mm, "Jira Test Case Generator 2.0.0 — Documentation technique")
    canvas.drawRightString(WIDTH - MARGIN, 8.6 * mm, f"page {canvas.getPageNumber()}")
    canvas.setFillColor(VIOLET)
    canvas.rect(0, HEIGHT - 5 * mm, WIDTH, 5 * mm, fill=1, stroke=0)
    canvas.restoreState()


class Doc(BaseDocTemplate):
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        frame = Frame(MARGIN, 18 * mm, CONTENT_WIDTH, HEIGHT - 18 * mm - 24 * mm, id="content")
        cover_frame = Frame(MARGIN, 20 * mm, CONTENT_WIDTH, 40 * mm, id="cover")
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[cover_frame], onPage=draw_cover),
            PageTemplate(id="content", frames=[frame], onPage=draw_content),
        ])

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            name = flowable.style.name
            if name == "H1":
                self.notify("TOCEntry", (0, flowable.getPlainText(), self.page))
            elif name == "H2":
                self.notify("TOCEntry", (1, flowable.getPlainText(), self.page))


# --------------------------------------------------------------------------
# Content
# --------------------------------------------------------------------------
def build():
    story = [NextPageTemplate("content"), Spacer(1, 1), PageBreak()]

    # --- Executive summary
    story += h1("1. Résumé exécutif")
    story.append(p(
        "La version 1 du <b>Jira Test Case Generator</b> démontrait une idée prometteuse : lire une user story "
        "Jira et confier à un modèle local la rédaction de cas de test. Elle n'était cependant pas exploitable "
        "en l'état : un <b>token Jira était commité en clair</b>, la dépendance Spring AI pointait vers un "
        "instantané de développement aujourd'hui introuvable, la réponse de l'API était du texte libre, et "
        "aucun test ne couvrait le comportement."))
    story.append(Spacer(1, 8))
    story.append(p(
        "La version 2.0.0 est une <b>réécriture complète</b> qui conserve le cœur fonctionnel — Spring Boot, "
        "Jira, Ollama — et ajoute ce qui manquait pour un outil réel : un contrat d'API typé et documenté, "
        "une extraction robuste des critères d'acceptation, une gestion d'erreurs normalisée, une interface "
        "web, une image Docker, une configuration sans secret, et <b>37 tests automatisés</b> dont un test "
        "d'intégration HTTP de bout en bout."))
    story.append(Spacer(1, 12))

    kpis = [
        ["Indicateur", "Valeur"],
        ["Tests automatisés", "37 (unitaires + intégration HTTP)"],
        ["Dépendances obsolètes ou SNAPSHOT", "0"],
        ["Secrets présents dans le dépôt", "0"],
        ["Statuts HTTP distincts gérés", "400 · 404 · 502 · 503 · 500"],
        ["Formats d'export", "JSON · CSV · Markdown"],
        ["Temps de démarrage mesuré", "3,8 s (JAR, JVM 17)"],
        ["Génération mesurée (stub local)", "232 ms pour 6 cas"],
    ]
    story.append(table(kpis, [80 * mm, CONTENT_WIDTH - 80 * mm]))
    story.append(Spacer(1, 10))
    story.append(callout(
        "Point d'attention critique",
        "Le token Atlassian présent dans l'archive d'origine doit être considéré comme compromis. "
        "Il doit être révoqué depuis la console Atlassian puis remplacé par un token frais fourni "
        "uniquement par variable d'environnement. La version 2 ne contient plus aucun secret.",
        color=ROSE, background=colors.HexColor("#FFF1F2")))

    # --- Context
    story.append(PageBreak())
    story += h1("2. Contexte et objectifs")
    story.append(h2("2.1 Le besoin"))
    story.append(p(
        "Dans une équipe Agile, une story Jira doit être transformée en plan de test exécutable. Ce travail "
        "est répétitif : identifier le chemin nominal, imaginer les cas d'erreur, les valeurs limites, les "
        "risques de sécurité et d'accessibilité, puis rédiger des étapes reproductibles. La qualité du résultat "
        "dépend fortement de la disponibilité et de l'expérience du testeur."))
    story.append(Spacer(1, 6))
    story.append(p(
        "L'automatisation visée n'est pas de remplacer le QA, mais de produire une <b>première trame complète</b> "
        "que le testeur valide, ajuste et enrichit. Le modèle doit rester <b>local</b> : les descriptions Jira "
        "contiennent souvent des informations métier sensibles."))
    story.append(h2("2.2 Objectifs de la refonte"))
    story += bullets([
        "<b>Fiabilité</b> : construire et démarrer sans dépendance à un snapshot, sans secret dans le code.",
        "<b>Contrat clair</b> : renvoyer du JSON typé, exploitable par une UI, un script ou un pipeline CI.",
        "<b>Robustesse</b> : couvrir les cas Jira Cloud et Server, les descriptions ADF, les réponses IA imparfaites.",
        "<b>Observabilité</b> : erreurs normalisées, logs utiles, sonde de santé, endpoint de configuration.",
        "<b>Expérience</b> : une interface web simple, des exports, un historique local.",
        "<b>Qualité</b> : des tests qui protègent réellement le comportement, exécutables sans Jira ni GPU.",
    ])
    story.append(h2("2.3 Périmètre"))
    story.append(p(
        "Le périmètre couvre la lecture d'une story unique par clé, la génération de cas de test et leur "
        "export. Ne sont volontairement pas inclus : la persistance en base, l'écriture dans Jira/Xray, "
        "l'authentification multi-utilisateurs et l'exécution des tests. Ces sujets sont traités dans la "
        "feuille de route en section 13."))

    # --- Audit
    story.append(PageBreak())
    story += h1("3. Audit de la version 1")
    story.append(p(
        "L'audit a porté sur les 16 fichiers de l'archive d'origine. Les constats ci-dessous sont classés par "
        "impact décroissant. Chaque ligne de la colonne « traitement » renvoie à une décision d'architecture "
        "concrète de la version 2."))
    story.append(Spacer(1, 8))
    audit = [
        ["#", "Constat", "Sévérité", "Traitement en v2"],
        ["1", "Token API Jira et email en clair dans application.properties", "Critique",
         "Supprimés du dépôt, variables d'environnement, .env ignoré, rotation documentée"],
        ["2", "Dépendance spring-ai 1.0.0-SNAPSHOT + dépôts snapshot", "Critique",
         "Spring Boot 3.5.16 + Spring AI 1.1.8 (BOM stable, versions épinglées)"],
        ["3", "Aucun test de comportement (contextLoads uniquement)", "Élevée",
         "37 tests : parseurs, client Jira, prompts, service, intégration HTTP"],
        ["4", "Réponse texte brut, HTTP 200 même en erreur", "Élevée",
         "DTO JSON + ProblemDetail RFC 7807 + statuts 400/404/502/503/500"],
        ["5", "Description ADF Jira Cloud interprétée comme du texte", "Élevée",
         "AdfTextExtractor : paragraphes, titres, listes, sauts de ligne"],
        ["6", "Aucune validation de la clé de story", "Moyenne",
         "Regex PROJET-123, normalisation, bornes sur maxCases"],
        ["7", "exception avalée, message générique sans diagnostic", "Moyenne",
         "Exceptions métier typées, codes stables, logs ciblés, messages actionnables"],
        ["8", "Démarrage impossible sans credentials (validation en bean)", "Moyenne",
         "Démarrage tolérant, état exposé par /api/v1/config, 503 à l'usage"],
        ["9", "Dépendances Jira client/Jersey/Jackson redondantes", "Moyenne",
         "RestClient Spring, timeouts explicites, aucune dépendance superflue"],
        ["10", "defaultFunctions déprécié, API Spring AI obsolète", "Moyenne",
         "ChatClient moderne, aucun appel déprécié"],
        ["11", "Sortie IA non contrainte, non parsable", "Moyenne",
         "Contrat JSON strict, parseur tolérant, erreur AI_RESPONSE_INVALID"],
        ["12", "Aucune protection contre l'injection de prompt", "Faible",
         "Contexte délimité, troncature, consigne « données non fiables »"],
        ["13", "Pas d'interface, pas de packaging, pas de documentation", "Faible",
         "UI responsive, Dockerfile, compose, README, PDF, présentation"],
    ]
    story.append(table(audit, [8 * mm, 62 * mm, 17 * mm, CONTENT_WIDTH - 87 * mm], font_size=7.6, padding=4))

    # --- Architecture
    story.append(PageBreak())
    story += h1("4. Architecture cible")
    story.append(p(
        "Le code est organisé par responsabilité : <b>web</b> (contrat HTTP), <b>service</b> (orchestration), "
        "<b>jira</b> (intégration distante), <b>ai</b> (prompting et parsing), <b>config</b> (propriétés), "
        "<b>error</b> (exceptions métier). Les dépendances vont toujours de l'extérieur vers l'intérieur."))
    story.append(Spacer(1, 4))
    story.append(architect_drawing())
    story.append(Paragraph("Figure 1 — Flux applicatif de la requête HTTP jusqu'à la réponse structurée.", S["caption"]))
    story.append(Spacer(1, 8))
    story.append(h2("4.1 Composants principaux"))
    components = [
        ["Composant", "Rôle", "Décision notable"],
        ["TestCaseController", "Expose /api/v1/test-cases", "Alias /jira-story conservé pour la compatibilité"],
        ["TestSuiteService", "Valide, orchestre, mappe", "Aucune logique HTTP dans les couches basses"],
        ["JiraRestClient", "Lit l'issue distante", "RestClient, Basic auth, timeouts, ADF + v2"],
        ["AcceptanceCriteriaExtractor", "Isole les critères", "Section FR/EN, inline, champ custom, fallback"],
        ["PromptFactory", "Construit les prompts", "Garde-fou anti-injection, troncature, contrat JSON"],
        ["TestCaseGenerationService", "Appelle le modèle", "Bornes, avertissements, mesure de durée"],
        ["TestCaseResponseParser", "Parse la sortie IA", "Fences, alias, prose, entrées partielles"],
        ["ApiExceptionHandler", "Normalise les erreurs", "RFC 7807, code stable, pas de fuite interne"],
    ]
    story.append(table(components, [48 * mm, 50 * mm, CONTENT_WIDTH - 98 * mm], font_size=7.6, padding=4))

    story.append(PageBreak())
    story += h1("5. Flux de génération")
    story.append(p(
        "Une requête suit huit étapes déterministes. Chaque étape peut échouer avec un code distinct, ce qui "
        "permet à l'appelant de réagir précisément sans lire un message libre."))
    steps = [
        ["Étape", "Action", "Échec possible"],
        ["1", "Validation de storyKey, langue, format, maxCases", "VALIDATION_ERROR (400)"],
        ["2", "Lecture de l'issue Jira avec Basic auth et timeout", "STORY_NOT_FOUND (404), JIRA_AUTH_FAILED (502)"],
        ["3", "Aplatissement de la description ADF ou texte", "JIRA_UNAVAILABLE (502)"],
        ["4", "Extraction des critères d'acceptation", "Repli documenté sur la description"],
        ["5", "Construction du prompt borné et sécurisé", "—"],
        ["6", "Appel du modèle Ollama local", "AI_UNAVAILABLE (503)"],
        ["7", "Parsing JSON tolérant et troncature", "AI_RESPONSE_INVALID (502)"],
        ["8", "Sérialisation du DTO de réponse", "INTERNAL_ERROR (500)"],
    ]
    story.append(table(steps, [14 * mm, 92 * mm, CONTENT_WIDTH - 106 * mm], font_size=7.9))
    story.append(Spacer(1, 12))
    story.append(h2("5.1 Exemple de requête"))
    story.append(code_block(
        'curl "http://localhost:8080/api/v1/test-cases?storyKey=KAN-3&language=FR&format=STANDARD&maxCases=6"'))
    story.append(Spacer(1, 8))
    story.append(h2("5.2 Extrait de réponse"))
    story.append(code_block(
        '{\n'
        '  "story": {\n'
        '    "key": "KAN-3",\n'
        '    "summary": "Connexion utilisateur",\n'
        '    "acceptanceCriteriaSource": "description-section"\n'
        '  },\n'
        '  "generation": { "model": "mistral", "language": "FR", "durationMs": 8421 },\n'
        '  "testCases": [\n'
        '    { "id": "TC-001", "title": "Connexion réussie", "type": "Fonctionnel",\n'
        '      "priority": "Haute", "steps": ["Ouvrir la page", "Saisir les identifiants"],\n'
        '      "expectedResult": "Le tableau de bord s\'affiche" }\n'
        '  ],\n'
        '  "warnings": []\n'
        '}'))
    story.append(Spacer(1, 10))
    story.append(callout(
        "Pourquoi un contrat JSON strict ?",
        "Un LLM local produit facilement des réponses légèrement différentes d'un appel à l'autre. "
        "En imposant un schéma et en parsant la sortie de façon tolérante, l'application transforme une "
        "sortie probabiliste en données déterministes : l'interface, les exports et les tests deviennent "
        "stables.", color=INDIGO, background=colors.HexColor("#EEF2FF")))

    # --- Stack
    story.append(PageBreak())
    story += h1("6. Stack technique")
    stack = [
        ["Composant", "Version", "Rôle et justification"],
        ["Java", "17 (Temurin)", "LTS, compatibilité Spring Boot 3.x"],
        ["Spring Boot", "3.5.16", "Web, validation, actuator, packaging exécutable"],
        ["Spring AI", "1.1.8", "Abstraction ChatClient et connecteur Ollama, version stable"],
        ["Gradle", "8.8 (wrapper)", "Build reproductible, aucun outil global requis"],
        ["Jira REST API", "v3 Cloud / v2 Server", "Lecture des issues, ADF ou texte brut"],
        ["Ollama", "courant", "Inférence locale, aucune donnée envoyée à un tiers"],
        ["JUnit 5 / AssertJ", "via Boot BOM", "Tests unitaires expressifs"],
        ["MockWebServer", "4.12.0", "Simulation HTTP de Jira, tests sans tenant"],
        ["HTML / CSS / JS", "natif", "Interface sans étape de build ni dépendance CDN"],
        ["Docker", "multi-stage", "Image JRE non-root, healthcheck"],
    ]
    story.append(table(stack, [42 * mm, 34 * mm, CONTENT_WIDTH - 76 * mm], font_size=8))
    story.append(Spacer(1, 10))
    story.append(p(
        "Le choix de supprimer le client Jira officiel et Jersey mérite une explication : l'application "
        "n'utilise qu'un endpoint, <font name='%s'>GET /rest/api/{version}/issue/{key}</font>. Le client "
        "officiel apporte un graphe de dépendances important, des conflits Jakarta et une surface d'API "
        "inutile. Spring <font name='%s'>RestClient</font> couvre le besoin en quelques lignes, avec des "
        "timeouts explicites et un contrôle total sur les erreurs." % (FONT_MONO, FONT_MONO)))

    # --- Interface
    story.append(PageBreak())
    story += h1("7. Interface web")
    story.append(p(
        "L'interface est servie directement par Spring Boot depuis <font name='%s'>src/main/resources/static</font>. "
        "Elle ne dépend d'aucun CDN, d'aucune police distante et d'aucun build front-end : elle fonctionne "
        "dans un réseau isolé, ce qui est cohérent avec le positionnement « IA locale »." % FONT_MONO))
    story.append(picture("ui-resultats.png", width=CONTENT_WIDTH,
                         caption="Figure 2 — Vue des résultats : story, métadonnées de génération, cas de test et exports."))
    story.append(Spacer(1, 6))
    story.append(h2("7.1 Fonctions de l'interface"))
    story += bullets([
        "Formulaire validé côté client et côté serveur (clé, langue, format, nombre de cas).",
        "Indicateurs de configuration Jira et de modèle, bannière explicite si Jira n'est pas configuré.",
        "Rendu des cas en cartes : type, priorité, préconditions, étapes numérotées, données, résultat attendu.",
        "Exports JSON, CSV (séparateur « ; », BOM UTF-8 pour Excel) et Markdown ; copie d'un cas ou de tous.",
        "Historique des huit dernières générations, stocké uniquement dans le navigateur.",
        "Gestion des états : chargement avec chronomètre, erreurs actionnables, avertissements non bloquants.",
        "Accessibilité : libellés, focus visible, navigation clavier, respect de prefers-reduced-motion.",
    ])


    # --- API
    story.append(PageBreak())
    story += h1("8. Référence API")
    endpoints = [
        ["Méthode", "Chemin", "Description"],
        ["GET", "/api/v1/test-cases", "Génère les cas de test d'une story"],
        ["GET", "/api/v1/jira-story", "Alias rétrocompatible de l'endpoint précédent"],
        ["GET", "/api/v1/config", "Configuration publique, sans secret"],
        ["GET", "/actuator/health", "Sonde de santé (Docker, Kubernetes)"],
        ["GET", "/", "Interface web"],
    ]
    story.append(table(endpoints, [18 * mm, 62 * mm, CONTENT_WIDTH - 80 * mm], font_size=8.2))
    story.append(Spacer(1, 10))
    story.append(h2("8.1 Paramètres"))
    params = [
        ["Paramètre", "Requis", "Défaut", "Valeurs"],
        ["storyKey", "Oui", "—", "PROJET-123"],
        ["language", "Non", "FR", "FR, EN"],
        ["format", "Non", "STANDARD", "STANDARD, GHERKIN"],
        ["maxCases", "Non", "8", "1 à 20 (configurable)"],
    ]
    story.append(table(params, [34 * mm, 22 * mm, 22 * mm, CONTENT_WIDTH - 78 * mm], font_size=8.2))
    story.append(Spacer(1, 10))
    story.append(h2("8.2 Codes d'erreur"))
    errors = [
        ["Code", "HTTP", "Cause", "Action recommandée"],
        ["VALIDATION_ERROR", "400", "Paramètre absent ou invalide", "Corriger la requête"],
        ["STORY_NOT_FOUND", "404", "Clé inconnue ou projet non autorisé", "Vérifier la clé et les droits"],
        ["JIRA_AUTH_FAILED", "502", "401/403 renvoyé par Jira", "Régénérer le token Atlassian"],
        ["JIRA_UNAVAILABLE", "502", "Timeout, 5xx, réponse illisible", "Vérifier URL, réseau, version d'API"],
        ["JIRA_NOT_CONFIGURED", "503", "Variables JIRA_* absentes", "Compléter la configuration"],
        ["AI_UNAVAILABLE", "503", "Ollama arrêté ou modèle absent", "ollama serve puis ollama pull"],
        ["AI_RESPONSE_INVALID", "502", "Sortie du modèle non exploitable", "Réessayer ou changer de modèle"],
        ["INTERNAL_ERROR", "500", "Erreur inattendue", "Consulter les logs serveur"],
    ]
    story.append(table(errors, [38 * mm, 14 * mm, 58 * mm, CONTENT_WIDTH - 110 * mm], font_size=7.7))

    # --- Security
    story.append(PageBreak())
    story += h1("9. Sécurité et configuration")
    story.append(callout(
        "À faire immédiatement : révoquer le token exposé",
        "L'archive d'origine contenait un email et un token API Jira en clair dans application.properties. "
        "Même si le dépôt est privé, considérez ce token comme compromis : révoquez-le depuis "
        "id.atlassian.com, générez-en un nouveau, et ne le placez que dans un fichier .env local ou un "
        "gestionnaire de secrets (Vault, AWS Secrets Manager, GitHub Actions Secrets).",
        color=ROSE, background=colors.HexColor("#FFF1F2")))
    story.append(Spacer(1, 10))
    story.append(h2("9.1 Mesures appliquées"))
    story += bullets([
        "Aucune credential dans le code, les tests, les ressources ou les logs.",
        "Fichier <font name='%s'>.env</font> ignoré par Git ; <font name='%s'>.env.example</font> fournit le contrat." % (FONT_MONO, FONT_MONO),
        "<font name='%s'>/api/v1/config</font> n'expose que des indicateurs (booléen, URL, version)." % FONT_MONO,
        "Validation des entrées avant tout appel distant ; bornes sur la taille et le nombre.",
        "Timeouts de connexion et de lecture côté Jira pour éviter l'épuisement de threads.",
        "Contexte story délimité et tronqué ; consigne explicite de ne jamais suivre ses instructions.",
        "Rendu de l'interface via textContent, jamais innerHTML avec des données distantes.",
        "Exceptions internes journalisées côté serveur, messages client sans détail sensible.",
        "Conteneur Docker non-root, healthcheck, aucune socket ou volume inutile.",
    ])
    story.append(Spacer(1, 8))
    story.append(h2("9.2 Variables d'environnement"))
    env = [
        ["Variable", "Défaut", "Rôle"],
        ["JIRA_BASE_URL", "—", "URL de l'instance, avec ou sans /rest/api/3"],
        ["JIRA_EMAIL", "—", "Compte Atlassian (Basic auth)"],
        ["JIRA_API_TOKEN", "—", "Token API, jamais commité"],
        ["JIRA_API_VERSION", "3", "3 = Cloud, 2 = Server/Data Center"],
        ["JIRA_ACCEPTANCE_CRITERIA_FIELD", "—", "Champ custom des critères d'acceptation"],
        ["JIRA_TIMEOUT", "15s", "Connect et read timeout"],
        ["OLLAMA_BASE_URL", "http://localhost:11434", "Endpoint Ollama"],
        ["AI_MODEL", "mistral", "Modèle utilisé"],
        ["AI_TEMPERATURE", "0.2", "Créativité du modèle"],
        ["GENERATION_MAX_TEST_CASES", "20", "Plafond dur de cas par requête"],
    ]
    story.append(table(env, [62 * mm, 44 * mm, CONTENT_WIDTH - 106 * mm], font_size=7.7))
    story.append(Spacer(1, 8))
    story.append(p(
        "L'application démarre volontairement sans credentials. Cela permet de valider l'installation, "
        "d'afficher un diagnostic clair et de déployer l'image avant de brancher les secrets. L'erreur "
        "n'apparaît qu'au moment de l'usage, avec un code 503 et la liste des variables manquantes."))

    # --- Tests
    story.append(PageBreak())
    story += h1("10. Qualité et tests")
    story.append(p(
        "La suite compte <b>37 tests</b>, exécutés avec <font name='%s'>./gradlew test</font>. Le test "
        "d'intégration démarre le contexte Spring complet sur un port aléatoire, expose les vrais endpoints "
        "HTTP, remplace Jira par MockWebServer et le modèle par un ChatModel factice. Aucun tenant Atlassian, "
        "aucun GPU et aucune connexion externe ne sont nécessaires." % FONT_MONO))
    story.append(Spacer(1, 8))
    tests = [
        ["Suite", "Tests", "Ce qu'elle protège"],
        ["AdfTextExtractorTest", "4", "ADF Cloud, texte v2, nœuds inconnus, null"],
        ["AcceptanceCriteriaExtractorTest", "6", "Sections FR/EN, inline, fallback, section vide"],
        ["JiraRestClientTest", "7", "Mapping, Basic auth, champ custom, 404/401/500, URL legacy"],
        ["TestCaseResponseParserTest", "6", "Fences, tableau nu, alias, prose, entrées invalides"],
        ["PromptFactoryTest", "4", "Contenu, Gherkin/EN, troncature, critères absents"],
        ["TestCaseGenerationServiceTest", "6", "Limites, avertissements, erreurs IA"],
        ["ApiIntegrationTest", "8", "Contrat HTTP, erreurs, config, UI, health"],
        ["Total", "37", "Tous verts au 9 novembre 2026"],
    ]
    story.append(table(tests, [62 * mm, 14 * mm, CONTENT_WIDTH - 76 * mm], font_size=8))
    story.append(Spacer(1, 10))
    story.append(h2("10.1 Vérification manuelle"))
    story.append(p(
        "Au-delà des tests automatisés, l'application a été lancée contre un Jira simulé et un Ollama simulé, "
        "puis pilotée dans un navigateur Chromium en 1440 × 1000. La génération a produit 6 cas en 232 ms, "
        "les exports JSON, CSV et Markdown ont été déclenchés, et les parcours d'erreur 404 et 401 ont été "
        "observés. Les captures de ce document proviennent de cette exécution."))
    story.append(Spacer(1, 8))
    story.append(h2("10.2 Limites de la validation"))
    story += bullets([
        "Aucun tenant Jira réel ni modèle Ollama réel n'était disponible dans l'environnement de build ; "
        "les intégrations ont été validées contre des serveurs simulant les contrats HTTP.",
        "La qualité rédactionnelle des cas dépend du modèle choisi : mistral est un bon compromis, "
        "llama3.1 ou qwen2.5 produisent souvent un JSON plus fiable.",
        "Aucun test de charge n'a été réalisé : le goulot d'étranglement est l'inférence locale, non l'application.",
    ])
    story.append(Spacer(1, 6))
    story.append(code_block("./gradlew test --console=plain\n# 37 tests, 0 échec — BUILD SUCCESSFUL"))

    # --- Operations
    story.append(PageBreak())
    story += h1("11. Exploitation et déploiement")
    story.append(h2("11.1 Démarrage local"))
    story.append(code_block(
        "cp .env.example .env          # renseigner JIRA_*\n"
        "ollama pull mistral\n"
        "./gradlew bootRun             # http://localhost:8080"))
    story.append(Spacer(1, 8))
    story.append(h2("11.2 JAR autonome"))
    story.append(code_block(
        "./gradlew clean bootJar\n"
        "java -jar build/libs/jira-test-case-generator.jar"))
    story.append(Spacer(1, 8))
    story.append(h2("11.3 Docker Compose"))
    story.append(code_block(
        "cp .env.example .env\n"
        "docker compose up -d --build\n"
        "docker compose exec ollama ollama pull mistral"))
    story.append(Spacer(1, 8))
    story.append(p(
        "L'image est construite en deux étapes (Gradle puis JRE Alpine), s'exécute avec un utilisateur non "
        "privilégié et expose un healthcheck sur <font name='%s'>/actuator/health</font>. Le modèle est "
        "téléchargé explicitement : cette séparation évite de re-télécharger plusieurs gigaoctets à chaque "
        "redémarrage et rend le démarrage prévisible." % FONT_MONO))
    story.append(h2("11.4 Supervision"))
    story += bullets([
        "Sonde de disponibilité : <font name='%s'>GET /actuator/health</font> (statut UP/DOWN)." % FONT_MONO,
        "Version déployée : <font name='%s'>GET /actuator/info</font> et <font name='%s'>/api/v1/config</font>." % (FONT_MONO, FONT_MONO),
        "Logs : niveau INFO pour l'application, WARN pour Spring AI ; aucun token ni contenu intégral.",
        "Erreurs : chaque échec porte un code stable, facile à agréger dans un tableau de bord.",
    ])
    story.append(Spacer(1, 6))
    story.append(callout(
        "Recommandation de production",
        "Placez l'application derrière un reverse proxy TLS et une authentification (OIDC ou mTLS). "
        "Elle ne gère volontairement pas les comptes utilisateurs : c'est un outil interne, pas un service "
        "public. Restreignez également l'accès réseau à Jira et à Ollama.", color=AMBER,
        background=colors.HexColor("#FFFBEB")))

    # --- Performance
    story.append(PageBreak())
    story += h1("12. Performance et limites")
    perf = [
        ["Mesure", "Valeur observée", "Contexte"],
        ["Démarrage de l'application", "3,8 s", "JAR, JVM 17, contexte Spring complet"],
        ["Génération HTTP de bout en bout", "232 ms", "Jira et Ollama simulés, 6 cas"],
        ["Taille du JAR", "~45 Mo", "Spring Boot + Spring AI, modèle exclu"],
        ["Mémoire JVM", "~250 Mo", "MaxRAMPercentage fixé à 75 % en Docker"],
        ["Cas maximum par requête", "20", "Configurable, borne dure"],
        ["Contexte story maximum", "8 000 caractères", "Troncature explicite et signalée"],
    ]
    story.append(table(perf, [58 * mm, 38 * mm, CONTENT_WIDTH - 96 * mm], font_size=8))
    story.append(Spacer(1, 10))
    story.append(p(
        "Avec un vrai modèle local, la latence est dominée par l'inférence : comptez de 10 à 60 secondes "
        "pour 8 cas avec mistral sur un CPU récent, moins avec un GPU. L'application n'ajoute qu'un aller-retour "
        "Jira et un parsing JSON. Les timeouts HTTP sont réglés à 15 secondes pour Jira et 3 minutes pour le "
        "client Ollama afin d'absorber les générations longues."))
    story.append(Spacer(1, 6))
    story.append(h2("12.1 Limites connues"))
    story += bullets([
        "Un seul modèle et une seule story par requête ; pas de génération asynchrone.",
        "Pas de cache : une même story est relue et régénérée à chaque appel.",
        "Le parsing tolérant masque parfois une sortie partielle du modèle ; les avertissements le signalent.",
        "Les critères d'acceptation heuristiques peuvent inclure du contexte superflu si la story est mal structurée.",
        "Aucune persistance : l'historique vit dans le navigateur et disparaît avec lui.",
    ])

    # --- Roadmap
    story.append(PageBreak())
    story += h1("13. Feuille de route")
    roadmap = [
        ["Priorité", "Évolution", "Valeur attendue"],
        ["P1", "Export Xray / Zephyr (CSV d'import dédié)", "Supprimer la ressaisie dans l'outil de test"],
        ["P1", "Cache des stories Jira avec TTL", "Réduire la latence et les appels API"],
        ["P2", "Génération en streaming (SSE)", "Afficher les cas au fil de la réponse"],
        ["P2", "Persistance PostgreSQL des suites", "Historique partagé et traçabilité"],
        ["P2", "Lien direct story / suite de tests", "Traçabilité QA et audit"],
        ["P3", "Authentification SSO et quotas", "Ouvrir l'outil à plusieurs équipes"],
        ["P3", "Comparaison multi-modèles", "Choisir le modèle le plus pertinent"],
        ["P3", "Génération asynchrone pour stories longues", "Éviter les timeouts navigateur"],
    ]
    story.append(table(roadmap, [20 * mm, 78 * mm, CONTENT_WIDTH - 98 * mm], font_size=8))
    story.append(Spacer(1, 12))
    story.append(h2("13.1 Conclusion"))
    story.append(p(
        "La version 2 transforme une démonstration en outil utilisable : elle démarre sans secret, expose un "
        "contrat stable, tolère les imperfections d'un LLM local, affiche un diagnostic précis et se déploie "
        "en une commande. Les 37 tests et la vérification navigateur donnent une base saine pour les "
        "évolutions à venir, en particulier l'export vers les outils de gestion de tests."))

    # --- Annexes
    story.append(PageBreak())
    story += h1("14. Annexes")
    story.append(h2("14.1 Structure du projet"))
    story.append(code_block(
        "jira-test-case-generator/\n"
        "├── build.gradle, settings.gradle, gradle.properties\n"
        "├── Dockerfile, docker-compose.yml, .env.example\n"
        "├── README.md, LICENSE.md\n"
        "├── docs/                   # ce document, la présentation, les scripts\n"
        "└── src/\n"
        "    ├── main/java/com/asecurityguru/jiratestgen/\n"
        "    │   ├── ai/ jira/ service/ web/ config/ error/\n"
        "    └── main/resources/\n"
        "        ├── application.yml\n"
        "        └── static/          # index.html, css, js, favicon\n"
        "    └── test/java/           # 37 tests"))
    story.append(Spacer(1, 8))
    story.append(h2("14.2 Commandes utiles"))
    commands = [
        ["Commande", "Usage"],
        ["./gradlew test", "Exécuter les 37 tests"],
        ["./gradlew bootRun", "Lancer en développement"],
        ["./gradlew clean bootJar", "Construire le JAR exécutable"],
        ["docker compose up -d --build", "Démarrer l'application et Ollama"],
        ["curl localhost:8080/api/v1/config", "Vérifier la configuration détectée"],
        ["curl localhost:8080/actuator/health", "Vérifier la disponibilité"],
    ]
    story.append(table(commands, [72 * mm, CONTENT_WIDTH - 72 * mm], font_size=8))
    story.append(Spacer(1, 10))
    story.append(h2("14.3 Glossaire"))
    glossary = [
        ["Terme", "Définition"],
        ["ADF", "Atlassian Document Format : arbre JSON utilisé par Jira Cloud pour le texte enrichi."],
        ["Ollama", "Serveur d'inférence local exposant une API HTTP compatible avec plusieurs modèles."],
        ["Critère d'acceptation", "Condition observable qui définit la réussite d'une story."],
        ["RFC 7807", "Standard des réponses d'erreur HTTP (application/problem+json)."],
        ["Gherkin", "Syntaxe Given/When/Then utilisée par les outils BDD."],
        ["Prompt injection", "Tentative de faire exécuter des instructions malveillantes via des données."],
    ]
    story.append(table(glossary, [40 * mm, CONTENT_WIDTH - 40 * mm], font_size=7.8))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        f"Jira Test Case Generator 2.0.0 — document généré le {date.today().strftime('%d/%m/%Y')} "
        "avec reportlab. Sources : dépôt du projet.", S["small"]))

    # --- TOC (placed after build via multiBuild)
    toc = TableOfContents()
    toc.levelStyles = [S["toc1"], S["toc2"]]
    toc.dotsMinLevel = 0

    # Insert TOC at beginning (after cover)
    toc_page = [Paragraph("Sommaire", S["toctitle"]), Spacer(1, 4),
                Table([[""]], colWidths=[CONTENT_WIDTH], rowHeights=[1.6],
                      style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), VIOLET),
                                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0)])),
                Spacer(1, 14), toc, PageBreak()]
    story = story[:3] + toc_page + story[3:]

    doc = Doc(OUTPUT, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
              topMargin=24 * mm, bottomMargin=18 * mm,
              title="Jira Test Case Generator — Documentation technique",
              author="Alex Alkhatib", subject="Documentation technique v2.0.0")
    doc.multiBuild(story)
    print(f"PDF written: {OUTPUT}")


if __name__ == "__main__":
    build()
