#!/usr/bin/env python3
"""Generate the project presentation (PPTX) for Jira Test Case Generator 2.0.0.

Requirements: python-pptx, pillow
Usage: python generate_presentation.py
"""
from __future__ import annotations

import os
import random

from PIL import Image, ImageDraw, ImageFilter
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(HERE, "Jira-Test-Case-Generator-Presentation.pptx")
IMAGES = os.path.join(HERE, "images")
BUILD = os.path.join(HERE, ".build")
os.makedirs(BUILD, exist_ok=True)

W, H = 13.333, 7.5
NAVY = RGBColor(0x07, 0x0B, 0x16)
NAVY_2 = RGBColor(0x0D, 0x15, 0x27)
CARD = RGBColor(0x13, 0x1D, 0x33)
TEXT = RGBColor(0xE8, 0xEE, 0xFB)
SOFT = RGBColor(0xA5, 0xB4, 0xCB)
MUTED = RGBColor(0x64, 0x74, 0x8B)
VIOLET = RGBColor(0x8B, 0x5C, 0xF6)
VIOLET_L = RGBColor(0xC4, 0xB5, 0xFD)
CYAN = RGBColor(0x22, 0xD3, 0xEE)
EMERALD = RGBColor(0x34, 0xD3, 0x99)
AMBER = RGBColor(0xFB, 0xBF, 0x24)
ROSE = RGBColor(0xFB, 0x71, 0x85)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "Calibri"


# --------------------------------------------------------------------------
# Backgrounds (generated with Pillow, reused by every slide)
# --------------------------------------------------------------------------
def make_background(path: str, title: bool = False):
    width, height = 1920, 1080
    base = Image.new("RGB", (width, height), (7, 11, 22))
    draw = ImageDraw.Draw(base)
    for y in range(height):
        ratio = y / height
        r = int(7 + 8 * ratio)
        g = int(11 + 10 * ratio)
        b = int(22 + 14 * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    glow = Image.new("RGB", (width, height), (0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    if title:
        gdraw.ellipse([-380, -420, 760, 620], fill=(82, 36, 168))
        gdraw.ellipse([1180, -320, 2200, 620], fill=(9, 82, 120))
        gdraw.ellipse([760, 700, 1500, 1320], fill=(12, 70, 70))
    else:
        gdraw.ellipse([-500, -500, 520, 420], fill=(52, 24, 96))
        gdraw.ellipse([1500, 700, 2300, 1400], fill=(8, 58, 78))
    glow = glow.filter(ImageFilter.GaussianBlur(190))
    base = Image.blend(base, Image.composite(glow, base, glow.convert("L")), 0.55 if title else 0.38)

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    for x in range(0, width, 72):
        odraw.line([(x, 0), (x, height)], fill=(148, 163, 184, 10), width=1)
    for y in range(0, height, 72):
        odraw.line([(0, y), (width, y)], fill=(148, 163, 184, 10), width=1)
    base = Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")
    base.save(path, quality=92)


make_background(os.path.join(BUILD, "bg-title.jpg"), title=True)
make_background(os.path.join(BUILD, "bg-content.jpg"), title=False)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def new_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.shapes.add_picture(os.path.join(BUILD, "bg-content.jpg"), 0, 0, width=prs.slide_width, height=prs.slide_height)
    return slide


def textbox(slide, x, y, w, h, text, size=18, bold=False, color=TEXT, align=PP_ALIGN.LEFT,
            font=FONT, spacing=1.0, anchor=MSO_ANCHOR.TOP, italic=False):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.word_wrap = True
    frame.margin_left = 0
    frame.margin_right = 0
    frame.margin_top = 0
    frame.margin_bottom = 0
    frame.vertical_anchor = anchor
    lines = text.split("\n")
    for i, line in enumerate(lines):
        paragraph = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        paragraph.alignment = align
        paragraph.line_spacing = spacing
        run = paragraph.add_run()
        run.text = line
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.color.rgb = color
        run.font.name = font
    return box


def rect(slide, x, y, w, h, fill=CARD, line=None, radius=0.12, shape=MSO_SHAPE.ROUNDED_RECTANGLE, line_width=1):
    shp = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(line_width)
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        shp.adjustments[0] = radius
    shp.shadow.inherit = False
    return shp


def chip(slide, x, y, w, label, color=VIOLET, fill=None, size=11):
    rect(slide, x, y, w, 0.32, fill=fill or RGBColor(0x1E, 0x1B, 0x3B), line=color, radius=0.5)
    textbox(slide, x, y + 0.055, w, 0.24, label, size=size, bold=True, color=color, align=PP_ALIGN.CENTER)


def kicker(slide, text, color=CYAN):
    textbox(slide, 0.75, 0.46, 8.0, 0.3, text.upper(), size=11.5, bold=True, color=color)


def title(slide, text, y=0.78, size=31, width=11.8):
    textbox(slide, 0.75, y, width, 0.95, text, size=size, bold=True, color=WHITE)


def footer(slide, number):
    textbox(slide, 0.75, 7.03, 7.0, 0.28, "Jira Test Case Generator · v2.0.0", size=9, color=MUTED)
    textbox(slide, 11.35, 7.03, 1.25, 0.28, f"{number:02d} / 14", size=9, color=MUTED, align=PP_ALIGN.RIGHT)


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def card(slide, x, y, w, h, heading, body, accent=VIOLET, heading_size=15, body_size=11.5, icon=None):
    rect(slide, x, y, w, h, fill=CARD, line=RGBColor(0x24, 0x30, 0x4A), radius=0.07)
    rect(slide, x, y, 0.055, h, fill=accent, radius=0.5)
    textbox(slide, x + 0.28, y + 0.22, w - 0.5, 0.35, heading, size=heading_size, bold=True, color=WHITE)
    textbox(slide, x + 0.28, y + 0.72, w - 0.5, h - 0.85, body, size=body_size, color=SOFT, spacing=1.08)


def arrow(slide, x1, y1, x2, y2, color=RGBColor(0x47, 0x55, 0x69)):
    connector = slide.shapes.add_connector(1, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    connector.line.color.rgb = color
    connector.line.width = Pt(1.5)
    return connector


def table(slide, rows, x, y, w, col_widths, header_color=VIOLET, font_size=10.5, row_height=0.42):
    shape = slide.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), Inches(row_height * len(rows)))
    tbl = shape.table
    for i, width in enumerate(col_widths):
        tbl.columns[i].width = Inches(width)
    for r, row in enumerate(rows):
        tbl.rows[r].height = Inches(row_height)
        for c, value in enumerate(row):
            cell = tbl.cell(r, c)
            cell.margin_left = Inches(0.1)
            cell.margin_right = Inches(0.08)
            cell.margin_top = Inches(0.04)
            cell.margin_bottom = Inches(0.04)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            if r == 0:
                cell.fill.fore_color.rgb = RGBColor(0x1A, 0x12, 0x3A)
            else:
                cell.fill.fore_color.rgb = CARD if r % 2 else RGBColor(0x0F, 0x18, 0x2B)
            frame = cell.text_frame
            frame.word_wrap = True
            paragraph = frame.paragraphs[0]
            run = paragraph.add_run()
            run.text = str(value)
            run.font.size = Pt(font_size if r else font_size)
            run.font.bold = r == 0
            run.font.color.rgb = VIOLET_L if r == 0 else (TEXT if c == 0 else SOFT)
            run.font.name = FONT
    return tbl


# --------------------------------------------------------------------------
# Slides
# --------------------------------------------------------------------------
def build():
    prs = Presentation()
    prs.slide_width = Inches(W)
    prs.slide_height = Inches(H)

    # 1 — Title
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.shapes.add_picture(os.path.join(BUILD, "bg-title.jpg"), 0, 0, width=prs.slide_width, height=prs.slide_height)
    textbox(slide, 0.85, 1.15, 6.0, 0.3, "QA ENGINEERING  ·  GENAI  ·  SPRING BOOT", size=12, bold=True, color=CYAN)
    textbox(slide, 0.85, 1.68, 8.4, 1.9, "Jira Test Case\nGenerator", size=54, bold=True, color=WHITE, spacing=0.92)
    textbox(slide, 0.85, 3.62, 7.5, 0.9,
            "Transformez vos critères d'acceptation en cas de test\nfonctionnels structurés, avec une IA qui tourne en local.",
            size=16, color=SOFT, spacing=1.15)
    chip(slide, 0.87, 4.78, 1.35, "v2.0.0", color=CYAN, fill=RGBColor(0x08, 0x2A, 0x38))
    chip(slide, 2.32, 4.78, 2.25, "Spring Boot 3.5", color=VIOLET_L, fill=RGBColor(0x1B, 0x12, 0x38))
    chip(slide, 4.67, 4.78, 1.75, "Spring AI 1.1", color=VIOLET_L, fill=RGBColor(0x1B, 0x12, 0x38))
    textbox(slide, 0.85, 5.62, 6.2, 0.6, "Alex Alkhatib  ·  9 novembre 2026  ·  Licence MIT", size=11.5, color=MUTED)

    # decorative stack of cards
    rect(slide, 9.55, 1.55, 2.9, 3.9, fill=RGBColor(0x13, 0x1D, 0x33), line=RGBColor(0x3D, 0x2F, 0x6B), radius=0.06)
    rect(slide, 9.78, 1.34, 2.9, 3.9, fill=RGBColor(0x18, 0x22, 0x3D), line=RGBColor(0x4C, 0x3B, 0x82), radius=0.06)
    rect(slide, 10.02, 1.13, 2.9, 3.9, fill=RGBColor(0x0F, 0x18, 0x2B), line=CYAN, radius=0.06)
    for i, (width, color) in enumerate([(1.55, VIOLET), (2.1, RGBColor(0x44, 0x4B, 0x6B)), (1.25, RGBColor(0x44, 0x4B, 0x6B))]):
        rect(slide, 10.3, 1.45 + i * 0.5, width, 0.12, fill=color, radius=0.5, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    chip(slide, 10.3, 3.12, 1.5, "TC-001", color=EMERALD, fill=RGBColor(0x0A, 0x2A, 0x22), size=10)
    for i in range(3):
        textbox(slide, 10.3, 3.62 + i * 0.36, 2.35, 0.3, ["✓ Given un compte valide", "✓ When je me connecte", "✓ Then le dashboard s'affiche"][i],
                size=9.5, color=SOFT)
    textbox(slide, 9.9, 5.32, 3.2, 0.4, "37 tests · 0 secret · 1 JAR", size=11, bold=True, color=EMERALD, align=PP_ALIGN.CENTER)
    notes(slide, "Présenter le projet en une phrase : un outil interne qui lit une story Jira et produit une trame de test complète avec un modèle local. Insister sur la refonte complète en v2.0.0.")

    # 2 — Problem
    slide = new_slide(prs)
    kicker(slide, "Le constat")
    title(slide, "Le plan de test reste le maillon lent du cycle QA")
    problems = [
        ("20–45 min", "par story", "Rédiger un plan de test sérieux, hors exécution.", VIOLET),
        ("Couverture inégale", "selon le testeur", "Les cas négatifs et limites sont souvent oubliés.", CYAN),
        ("0 traçabilité", "story ↔ tests", "Les cas vivent dans un tableur, déconnectés de Jira.", AMBER),
        ("Risque RGPD", "données métier", "Envoyer les descriptions à un LLM public est exclu.", ROSE),
    ]
    x = 0.75
    for value, label, body, color in problems:
        rect(slide, x, 2.0, 2.9, 1.95, fill=CARD, line=RGBColor(0x24, 0x30, 0x4A), radius=0.07)
        rect(slide, x, 2.0, 2.9, 0.055, fill=color, radius=0.5)
        textbox(slide, x + 0.24, 2.22, 2.45, 0.5, value, size=18 if len(value) < 12 else 15, bold=True, color=WHITE)
        textbox(slide, x + 0.24, 2.72, 2.45, 0.28, label.upper(), size=8.5, bold=True, color=color)
        textbox(slide, x + 0.24, 3.08, 2.45, 0.75, body, size=10.5, color=SOFT, spacing=1.1)
        x += 3.06
    rect(slide, 0.75, 4.4, 11.85, 1.35, fill=RGBColor(0x0E, 0x17, 0x2A), line=RGBColor(0x2B, 0x3A, 0x55), radius=0.06)
    textbox(slide, 1.0, 4.62, 11.3, 0.95,
            "L'objectif n'est pas de remplacer le QA : c'est de produire une trame complète et cohérente,\n"
            "que le testeur valide, ajuste et enrichit — sans jamais sortir les données de l'entreprise.",
            size=14.5, color=TEXT, spacing=1.2)
    footer(slide, 2)
    notes(slide, "Ancrer le problème dans le quotidien : la rédaction manuelle est répétitive et la couverture dépend de la personne. Le point RGPD justifie le choix d'un modèle local.")

    # 3 — Audit
    slide = new_slide(prs)
    kicker(slide, "Audit de la v1", color=ROSE)
    title(slide, "Une preuve de concept, pas encore un outil")
    findings = [
        ("CRITIQUE", "Token Jira commité", "Email et token API en clair dans application.properties.", ROSE),
        ("CRITIQUE", "Build non reproductible", "Spring AI 1.0.0-SNAPSHOT et dépôts snapshot disparus.", ROSE),
        ("ÉLEVÉE", "Réponse non structurée", "Texte libre renvoyé en 200, même en cas d'erreur.", AMBER),
        ("ÉLEVÉE", "ADF mal interprété", "Description Cloud lue comme une chaîne vide.", AMBER),
        ("MOYENNE", "Zéro test utile", "Un seul contextLoads, aucune validation du flux.", CYAN),
        ("MOYENNE", "Dépendances redondantes", "Jira client + Jersey + Jackson, conflits Jakarta.", CYAN),
    ]
    positions = [(0.75, 1.95), (4.75, 1.95), (8.75, 1.95), (0.75, 3.75), (4.75, 3.75), (8.75, 3.75)]
    for (x, y), (severity, heading, body, color) in zip(positions, findings):
        rect(slide, x, y, 3.82, 1.55, fill=CARD, line=RGBColor(0x24, 0x30, 0x4A), radius=0.07)
        rect(slide, x, y, 0.05, 1.55, fill=color, radius=0.5)
        textbox(slide, x + 0.26, y + 0.19, 1.1, 0.24, severity, size=8.5, bold=True, color=color)
        textbox(slide, x + 0.26, y + 0.46, 3.35, 0.34, heading, size=14.5, bold=True, color=WHITE)
        textbox(slide, x + 0.26, y + 0.9, 3.3, 0.55, body, size=10.2, color=SOFT, spacing=1.05)
    textbox(slide, 0.75, 5.55, 11.8, 0.6,
            "16 fichiers audités  ·  13 constats documentés  ·  chaque constat a une contre-mesure en v2",
            size=12.5, color=MUTED)
    footer(slide, 3)
    notes(slide, "Ne pas s'attarder sur chaque ligne : montrer les deux critiques (secret + build cassé), puis annoncer que le reste structure la refonte.")

    # 4 — Solution
    slide = new_slide(prs)
    kicker(slide, "La refonte", color=EMERALD)
    title(slide, "Une chaîne déterministe, du Jira au JSON")
    steps = [
        ("01", "Lire", "Jira REST v3/v2\nADF aplati, critères isolés", VIOLET),
        ("02", "Comprendre", "Prompt borné + garde-fou\ncontre l'injection", CYAN),
        ("03", "Générer", "Ollama local\nJSON strict, 6 à 20 cas", EMERALD),
        ("04", "Livrer", "DTO typé, exports\nJSON / CSV / Markdown", AMBER),
    ]
    x = 0.75
    for i, (num, heading, body, color) in enumerate(steps):
        rect(slide, x, 2.05, 2.55, 1.85, fill=CARD, line=RGBColor(0x24, 0x30, 0x4A), radius=0.08)
        textbox(slide, x + 0.22, 2.18, 0.5, 0.3, num, size=11, bold=True, color=color)
        textbox(slide, x + 0.22, 2.5, 2.1, 0.35, heading, size=17, bold=True, color=WHITE)
        textbox(slide, x + 0.22, 2.98, 2.1, 0.75, body, size=10.5, color=SOFT, spacing=1.1)
        if i < 3:
            arrow(slide, x + 2.6, 2.97, x + 2.95, 2.97)
        x += 3.05
    rect(slide, 0.75, 4.3, 5.8, 1.8, fill=RGBColor(0x0E, 0x17, 0x2A), line=RGBColor(0x2B, 0x3A, 0x55), radius=0.06)
    textbox(slide, 1.0, 4.5, 5.3, 0.3, "CE QUI CHANGE", size=9.5, bold=True, color=CYAN)
    textbox(slide, 1.0, 4.82, 5.3, 1.15,
            "•  Contrat HTTP typé, erreurs RFC 7807\n"
            "•  Aucun secret : variables d'environnement\n"
            "•  Démarrage tolérant + diagnostic /config",
            size=11.5, color=SOFT, spacing=1.25)
    rect(slide, 6.8, 4.3, 5.8, 1.8, fill=RGBColor(0x0E, 0x17, 0x2A), line=RGBColor(0x2B, 0x3A, 0x55), radius=0.06)
    textbox(slide, 7.05, 4.5, 5.3, 0.3, "CE QUI RESTE", size=9.5, bold=True, color=EMERALD)
    textbox(slide, 7.05, 4.82, 5.3, 1.15,
            "•  Le cœur Spring Boot + Ollama\n"
            "•  L'endpoint /jira-story (alias)\n"
            "•  Le principe 100 % local",
            size=11.5, color=SOFT, spacing=1.25)
    footer(slide, 4)
    notes(slide, "Le message clé : on garde l'idée et la stack, on remplace tout ce qui empêchait la mise en production.")

    # 5 — Architecture
    slide = new_slide(prs)
    kicker(slide, "Architecture")
    title(slide, "Des couches explicites, testables isolément")
    layers = [
        ("web", "TestCaseController · ConfigController\nApiExceptionHandler · DTO", VIOLET, 0.75, 1.9),
        ("service", "TestSuiteService\nvalidation + orchestration", RGBColor(0x7C, 0x3A, 0xED), 3.95, 1.9),
        ("jira", "JiraRestClient · ADF\nAcceptanceCriteriaExtractor", AMBER, 7.15, 1.9),
        ("ai", "PromptFactory · Parser\nTestCaseGenerationService", EMERALD, 10.35, 1.9),
        ("config", "JiraProperties\nGenerationProperties · AiConfig", CYAN, 3.95, 4.25),
        ("error", "ApiException + 7 sous-types\ncodes stables → RFC 7807", ROSE, 7.15, 4.25),
    ]
    for name, body, color, x, y in layers:
        rect(slide, x, y, 2.82, 1.45, fill=CARD, line=RGBColor(0x24, 0x30, 0x4A), radius=0.07)
        rect(slide, x, y, 2.82, 0.055, fill=color, radius=0.5)
        textbox(slide, x + 0.22, y + 0.2, 2.4, 0.3, name, size=15, bold=True, color=color)
        textbox(slide, x + 0.22, y + 0.62, 2.4, 0.7, body, size=9.5, color=SOFT, spacing=1.1)
    arrow(slide, 3.57, 2.62, 3.9, 2.62)
    arrow(slide, 6.77, 2.62, 7.1, 2.62)
    arrow(slide, 9.97, 2.62, 10.3, 2.62)
    rect(slide, 0.75, 6.0, 11.85, 0.62, fill=RGBColor(0x0E, 0x17, 0x2A), line=RGBColor(0x2B, 0x3A, 0x55), radius=0.25)
    textbox(slide, 1.0, 6.14, 11.3, 0.35,
            "Dépendances unidirectionnelles  ·  aucun état partagé  ·  chaque brique se teste sans Spring",
            size=11.5, color=SOFT)
    footer(slide, 5)
    notes(slide, "Souligner la séparation : le client Jira ne connaît pas le prompt, le générateur ne connaît pas HTTP. C'est ce qui rend les 37 tests possibles.")

    # 6 — Stack
    slide = new_slide(prs)
    kicker(slide, "Stack & dépendances")
    title(slide, "Stable, minimal, reproductible")
    cards = [
        ("Java 17", "Temurin LTS", VIOLET),
        ("Spring Boot 3.5.16", "Web · Validation · Actuator", EMERALD),
        ("Spring AI 1.1.8", "ChatClient · Ollama", CYAN),
        ("Gradle 8.8", "Wrapper versionné", AMBER),
        ("Jira REST", "v3 Cloud · v2 Server", RGBColor(0x38, 0xBD, 0xF8)),
        ("JUnit 5 + MockWebServer", "37 tests sans dépendance externe", ROSE),
        ("HTML / CSS / JS", "UI sans build ni CDN", VIOLET_L),
        ("Docker multi-stage", "JRE Alpine non-root", EMERALD),
    ]
    for i, (name, body, color) in enumerate(cards):
        col, row = i % 4, i // 4
        x, y = 0.75 + col * 3.06, 1.95 + row * 1.6
        rect(slide, x, y, 2.86, 1.35, fill=CARD, line=RGBColor(0x24, 0x30, 0x4A), radius=0.07)
        rect(slide, x, y, 0.05, 1.35, fill=color, radius=0.5)
        textbox(slide, x + 0.24, y + 0.22, 2.45, 0.3, name, size=12.5, bold=True, color=WHITE)
        textbox(slide, x + 0.24, y + 0.65, 2.4, 0.55, body, size=10, color=SOFT)
    rect(slide, 0.75, 5.25, 11.85, 1.1, fill=RGBColor(0x0E, 0x17, 0x2A), line=RGBColor(0x2B, 0x3A, 0x55), radius=0.06)
    textbox(slide, 1.0, 5.45, 11.3, 0.75,
            "Supprimés : Jira Java Client, Jersey, dépendances Jackson explicites, SNAPSHOT.\n"
            "Remplacés par Spring RestClient + les starters Spring Boot déjà présents.",
            size=12, color=SOFT, spacing=1.2)
    footer(slide, 6)
    notes(slide, "Insister sur la reproductibilité : versions épinglées, pas de snapshot, wrapper Gradle inclus. Le build ne dépend pas de l'état d'un dépôt distant mouvant.")

    # 7 — Demo
    slide = new_slide(prs)
    kicker(slide, "Démonstration", color=EMERALD)
    title(slide, "De la clé KAN-3 à six cas de test")
    bullets = [
        ("Clé validée", "PROJET-123, normalisée en majuscules", VIOLET),
        ("Story lue", "ADF aplati, critères isolés", CYAN),
        ("6 cas générés", "nominal, négatif, sécurité, limites, a11y", EMERALD),
        ("Exports", "JSON, CSV Excel, Markdown", AMBER),
    ]
    y = 1.95
    for heading, body, color in bullets:
        rect(slide, 0.75, y, 3.55, 0.92, fill=CARD, line=RGBColor(0x24, 0x30, 0x4A), radius=0.08)
        rect(slide, 0.75, y, 0.05, 0.92, fill=color, radius=0.5)
        textbox(slide, 0.98, y + 0.13, 3.1, 0.28, heading, size=12, bold=True, color=WHITE)
        textbox(slide, 0.98, y + 0.48, 3.05, 0.35, body, size=9.5, color=SOFT)
        y += 1.08
    image_path = os.path.join(IMAGES, "ui-16x9.png")
    if not os.path.exists(image_path):
        image_path = os.path.join(IMAGES, "ui-resultats.png")
    if os.path.exists(image_path):
        rect(slide, 4.55, 1.75, 8.0, 4.65, fill=RGBColor(0x0F, 0x18, 0x2B), line=RGBColor(0x33, 0x41, 0x55), radius=0.04)
        slide.shapes.add_picture(image_path, Inches(4.66), Inches(1.86), width=Inches(7.78))
        textbox(slide, 4.66, 6.5, 7.8, 0.3, "Capture réelle — Chromium, Jira et Ollama simulés", size=8.5, color=MUTED)
    footer(slide, 7)
    notes(slide, "Montrer l'écran : la story à gauche du résultat, les cartes de cas, les exports. Mentionner que l'interface est servie par le même JAR.")

    # 8 — Features
    slide = new_slide(prs)
    kicker(slide, "Fonctionnalités")
    title(slide, "Ce que l'équipe QA peut faire dès aujourd'hui")
    features = [
        ("Lecture robuste", "Cloud (ADF) et Server (texte),\nchamp d'acceptance personnalisé.", VIOLET),
        ("Sortie exploitable", "ID, type, priorité, préconditions,\nétapes, données, résultat attendu.", CYAN),
        ("FR / EN + Gherkin", "Étapes impératives ou\nGiven/When/Then, au choix.", EMERALD),
        ("Exports", "JSON pour l'outillage,\nCSV pour Excel, MD pour la doc.", AMBER),
        ("Erreurs actionnables", "404, 401, timeout, Ollama absent :\nun code et une consigne.", ROSE),
        ("Zéro fuite", "Modèle local, pas d'appel SaaS,\nsecrets hors du code.", VIOLET_L),
    ]
    for i, (heading, body, color) in enumerate(features):
        col, row = i % 3, i // 3
        x, y = 0.75 + col * 4.06, 1.95 + row * 1.95
        rect(slide, x, y, 3.82, 1.7, fill=CARD, line=RGBColor(0x24, 0x30, 0x4A), radius=0.07)
        rect(slide, x, y, 3.82, 0.055, fill=color, radius=0.5)
        textbox(slide, x + 0.25, y + 0.24, 3.3, 0.3, heading, size=14, bold=True, color=WHITE)
        textbox(slide, x + 0.25, y + 0.68, 3.3, 0.85, body, size=10.2, color=SOFT, spacing=1.12)
    textbox(slide, 0.75, 5.85, 11.8, 0.5,
            "Le tout dans un seul JAR, sans base de données ni service externe.",
            size=12, color=MUTED)
    footer(slide, 8)
    notes(slide, "Passer rapidement : ce sont les bénéfices concrets pour l'équipe. Appuyer sur les exports et la gestion d'erreurs, qui font la différence avec une démo.")

    # 9 — API
    slide = new_slide(prs)
    kicker(slide, "Contrat d'API")
    title(slide, "Un endpoint, des données typées")
    table(slide, [
        ["Méthode", "Chemin", "Rôle"],
        ["GET", "/api/v1/test-cases", "Génération (storyKey, language, format, maxCases)"],
        ["GET", "/api/v1/jira-story", "Alias rétrocompatible"],
        ["GET", "/api/v1/config", "État public, sans secret"],
        ["GET", "/actuator/health", "Sonde de disponibilité"],
    ], 0.75, 1.85, 6.1, [0.85, 1.95, 3.3], font_size=10, row_height=0.48)
    rect(slide, 0.75, 4.3, 6.1, 1.75, fill=RGBColor(0x0E, 0x17, 0x2A), line=RGBColor(0x2B, 0x3A, 0x55), radius=0.06)
    textbox(slide, 0.98, 4.46, 5.65, 0.3, "ÉCHECS NORMALISÉS — RFC 7807", size=9, bold=True, color=ROSE)
    textbox(slide, 0.98, 4.75, 5.65, 1.2,
            "400 VALIDATION_ERROR   ·   404 STORY_NOT_FOUND\n"
            "502 JIRA_AUTH_FAILED   ·   503 AI_UNAVAILABLE\n"
            "502 AI_RESPONSE_INVALID   ·   500 INTERNAL_ERROR",
            size=10.5, color=SOFT, spacing=1.3, font="Consolas")
    rect(slide, 7.15, 1.85, 5.45, 4.55, fill=RGBColor(0x08, 0x0F, 0x1E), line=RGBColor(0x2B, 0x3A, 0x55), radius=0.04)
    textbox(slide, 7.4, 2.02, 5.0, 0.3, "RÉPONSE (EXTRAIT)", size=9, bold=True, color=CYAN)
    textbox(slide, 7.4, 2.38, 5.0, 3.9,
            '{\n'
            '  "story": {\n'
            '    "key": "KAN-3",\n'
            '    "summary": "Connexion utilisateur"\n'
            '  },\n'
            '  "generation": {\n'
            '    "model": "mistral",\n'
            '    "durationMs": 8421\n'
            '  },\n'
            '  "testCases": [{\n'
            '    "id": "TC-001",\n'
            '    "title": "Connexion réussie",\n'
            '    "priority": "Haute",\n'
            '    "steps": ["Ouvrir la page", ...],\n'
            '    "expectedResult": "Dashboard"\n'
            '  }],\n'
            '  "warnings": []\n'
            '}',
            size=10, color=RGBColor(0xA5, 0xF3, 0xD0), spacing=1.18, font="Consolas")
    footer(slide, 9)
    notes(slide, "Le contrat est volontairement plat et stable : l'UI, les exports et les futurs connecteurs Xray/Zephyr s'appuient dessus. Les codes d'erreur sont documentés dans le README.")

    # 10 — Security
    slide = new_slide(prs)
    kicker(slide, "Sécurité", color=ROSE)
    title(slide, "Le premier correctif est un secret révoqué")
    rect(slide, 0.75, 1.9, 5.85, 1.55, fill=RGBColor(0x2A, 0x0F, 0x1A), line=ROSE, radius=0.06)
    textbox(slide, 1.0, 2.08, 5.35, 0.3, "ACTION IMMÉDIATE", size=9, bold=True, color=ROSE)
    textbox(slide, 1.0, 2.4, 5.3, 0.9,
            "Le token Jira de la v1 est compromis.\nRévoquez-le, générez-en un nouveau,\nstockez-le hors du dépôt.",
            size=12, color=RGBColor(0xFE, 0xE2, 0xE2), spacing=1.2)
    measures = [
        ("Pas de secret dans le code", "Variables d'environnement, .env ignoré"),
        ("Diagnostic sans fuite", "/config expose un booléen, jamais un token"),
        ("Anti prompt-injection", "Story délimitée, tronquée, non fiable"),
        ("Interface sûre", "Rendu textContent, pas de HTML distant"),
        ("Entrées validées", "Regex, enums, bornes avant appel amont"),
        ("Conteneur durci", "Utilisateur non-root, healthcheck"),
    ]
    y = 1.9
    for heading, body in measures:
        rect(slide, 6.95, y, 5.65, 0.72, fill=CARD, line=RGBColor(0x24, 0x30, 0x4A), radius=0.1)
        textbox(slide, 7.15, y + 0.1, 2.5, 0.28, heading, size=10.5, bold=True, color=WHITE)
        textbox(slide, 9.55, y + 0.11, 2.9, 0.45, body, size=9, color=SOFT)
        y += 0.78
    textbox(slide, 0.75, 3.85, 5.85, 2.3,
            "La configuration reste simple :\n"
            "JIRA_BASE_URL · JIRA_EMAIL · JIRA_API_TOKEN\n"
            "JIRA_API_VERSION · JIRA_ACCEPTANCE_CRITERIA_FIELD\n"
            "OLLAMA_BASE_URL · AI_MODEL\n\n"
            "L'application démarre sans credentials et\n"
            "explique précisément ce qui manque (503).",
            size=11, color=SOFT, spacing=1.35)
    footer(slide, 10)
    notes(slide, "Commencer par l'action de révocation : c'est le point le plus important de toute la refonte. Puis énumérer les garde-fous, notamment l'injection de prompt.")

    # 11 — Tests
    slide = new_slide(prs)
    kicker(slide, "Qualité", color=EMERALD)
    title(slide, "37 tests, aucun accès externe requis")
    textbox(slide, 0.75, 1.85, 2.6, 1.3, "37", size=64, bold=True, color=EMERALD)
    textbox(slide, 0.8, 3.1, 2.6, 0.8, "tests verts\n9 novembre 2026", size=12, color=SOFT, spacing=1.15)
    textbox(slide, 0.8, 4.2, 2.75, 1.9,
            "Unitaires, client HTTP,\nparsing, prompts, service\net intégration complète.\n\nAucun tenant Jira,\naucun GPU, aucun réseau.",
            size=10.5, color=MUTED, spacing=1.2)
    table(slide, [
        ["Suite", "N", "Protection"],
        ["AdfTextExtractor", "4", "ADF, texte v2, nœuds inconnus"],
        ["AcceptanceCriteriaExtractor", "6", "Sections FR/EN, inline, fallback"],
        ["JiraRestClient", "7", "Mapping, auth, 404/401/500"],
        ["TestCaseResponseParser", "6", "Fences, alias, prose, invalides"],
        ["PromptFactory", "4", "Gherkin, troncature, critères absents"],
        ["TestCaseGenerationService", "6", "Limites, warnings, erreurs IA"],
        ["ApiIntegrationTest", "8", "Contrat HTTP, config, UI, health"],
    ], 3.85, 1.9, 8.7, [2.75, 0.55, 5.4], font_size=10, row_height=0.47)
    rect(slide, 3.85, 5.85, 8.7, 0.55, fill=RGBColor(0x0A, 0x24, 0x1C), line=RGBColor(0x14, 0x53, 0x3F), radius=0.2)
    textbox(slide, 4.05, 5.97, 8.35, 0.3,
            "./gradlew test  →  BUILD SUCCESSFUL  ·  0 échec", size=10.5, color=EMERALD, font="Consolas")
    footer(slide, 11)
    notes(slide, "Le test d'intégration est le plus important : MockWebServer remplace Jira, un ChatModel factice remplace Ollama, et on traverse le vrai contrôleur jusqu'au JSON.")

    # 12 — Results
    slide = new_slide(prs)
    kicker(slide, "Bilan", color=CYAN)
    title(slide, "Ce qui a réellement changé")
    metrics = [
        ("0", "secret dans le dépôt", ROSE),
        ("0", "dépendance SNAPSHOT", AMBER),
        ("37", "tests automatisés", EMERALD),
        ("3,8 s", "temps de démarrage", CYAN),
        ("232 ms", "génération mesurée*", VIOLET),
    ]
    x = 0.75
    for value, label, color in metrics:
        rect(slide, x, 1.95, 2.3, 1.65, fill=CARD, line=RGBColor(0x24, 0x30, 0x4A), radius=0.08)
        textbox(slide, x + 0.2, 2.15, 1.95, 0.6, value, size=27, bold=True, color=color)
        textbox(slide, x + 0.2, 2.85, 1.95, 0.6, label, size=9.5, color=SOFT, spacing=1.1)
        x += 2.4
    textbox(slide, 0.75, 3.9, 6.4, 0.3, "CE QUE L'ÉQUIPE Y GAGNE", size=9.5, bold=True, color=CYAN)
    textbox(slide, 0.75, 4.2, 6.3, 2.2,
            "•  Une trame de test complète en quelques minutes\n"
            "•  Une couverture homogène : nominal, négatif, limites\n"
            "•  Des exports directement réutilisables\n"
            "•  Un diagnostic clair quand Jira ou Ollama est absent\n"
            "•  Aucune donnée métier envoyée à un tiers",
            size=11.5, color=SOFT, spacing=1.35)
    textbox(slide, 7.55, 3.9, 5.0, 0.3, "LIMITES ASSUMÉES", size=9.5, bold=True, color=AMBER)
    textbox(slide, 7.55, 4.2, 5.0, 2.2,
            "•  Pas de cache ni de persistance en v2\n"
            "•  Une story à la fois, sans streaming\n"
            "•  Qualité dépendante du modèle local\n"
            "•  Pas de test de charge réalisé\n"
            "•  Validation faite sur Jira/Ollama simulés",
            size=11.5, color=SOFT, spacing=1.35)
    textbox(slide, 0.75, 6.55, 11.8, 0.28,
            "* Jira et Ollama simulés — la latence réelle dépend du modèle et du matériel.", size=8.5, color=MUTED)
    footer(slide, 12)
    notes(slide, "Être honnête sur les limites : pas de tenant réel ni de GPU dans l'environnement. Les chiffres 232 ms portent sur les stubs, ce qui isole bien la performance applicative.")

    # 13 — Roadmap
    slide = new_slide(prs)
    kicker(slide, "Suite")
    title(slide, "Trois horizons pour industrialiser l'outil")
    columns = [
        ("P1 · COURT TERME", VIOLET, ["Export Xray / Zephyr", "Cache des stories (TTL)", "Documentation d'exploitation"]),
        ("P2 · MOYEN TERME", CYAN, ["Streaming SSE", "Persistance PostgreSQL", "Lien story ↔ suite de tests"]),
        ("P3 · OUVERTURE", EMERALD, ["SSO et quotas", "Comparaison multi-modèles", "Génération asynchrone"]),
    ]
    x = 0.75
    for heading, color, items in columns:
        rect(slide, x, 1.95, 3.82, 3.9, fill=CARD, line=RGBColor(0x24, 0x30, 0x4A), radius=0.07)
        rect(slide, x, 1.95, 3.82, 0.06, fill=color, radius=0.5)
        textbox(slide, x + 0.28, 2.2, 3.2, 0.3, heading, size=10, bold=True, color=color)
        y = 2.75
        for item in items:
            textbox(slide, x + 0.28, y, 3.2, 0.55, f"•  {item}", size=11.5, color=SOFT, spacing=1.1)
            y += 0.72
        x += 4.06
    rect(slide, 0.75, 6.1, 11.85, 0.55, fill=RGBColor(0x0E, 0x17, 0x2A), line=RGBColor(0x2B, 0x3A, 0x55), radius=0.2)
    textbox(slide, 1.0, 6.22, 11.3, 0.3,
            "Prochaine étape recommandée : brancher un vrai tenant Jira et mesurer la qualité sur 10 stories réelles.",
            size=11, color=SOFT)
    footer(slide, 13)
    notes(slide, "Ne pas promettre toutes les cases : la prochaine étape concrète est la validation sur un vrai tenant et l'export Xray, qui supprime la ressaisie.")

    # 14 — Closing
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.shapes.add_picture(os.path.join(BUILD, "bg-title.jpg"), 0, 0, width=prs.slide_width, height=prs.slide_height)
    textbox(slide, 0.85, 1.6, 7.2, 0.35, "MERCI", size=12, bold=True, color=CYAN)
    textbox(slide, 0.85, 2.05, 8.4, 1.7,
            "Une story entre.\nUn plan de test sort.",
            size=38, bold=True, color=WHITE, spacing=1.02)
    textbox(slide, 0.85, 3.9, 7.6, 1.1,
            "Jira Test Case Generator 2.0.0 — Java 17, Spring Boot, Spring AI, Ollama.\n"
            "Documentation PDF et README inclus dans le dépôt.",
            size=13, color=SOFT, spacing=1.3)
    chip(slide, 0.87, 5.15, 1.55, "MIT License", color=EMERALD, fill=RGBColor(0x0A, 0x24, 0x1C))
    chip(slide, 2.57, 5.15, 1.75, "v2.0.0", color=CYAN, fill=RGBColor(0x08, 0x2A, 0x38))
    textbox(slide, 0.85, 5.9, 6.0, 0.4, "Alex Alkhatib  ·  9 novembre 2026", size=11, color=MUTED)
    rect(slide, 9.72, 2.2, 2.9, 2.9, fill=RGBColor(0x0F, 0x18, 0x2B), line=VIOLET, radius=0.08)
    textbox(slide, 9.95, 2.45, 2.45, 0.3, "DANS LE DÉPÔT", size=8.5, bold=True, color=VIOLET_L)
    textbox(slide, 9.95, 2.85, 2.45, 2.0,
            "README.md\n\nPDF technique\n\nPrésentation\n\nCode source + tests",
            size=11, color=SOFT, spacing=1.3)
    notes(slide, "Conclure sur la proposition de valeur et proposer une démonstration sur une story réelle de l'équipe.")

    prs.save(OUTPUT)
    print(f"PPTX written: {OUTPUT} ({len(prs.slides._sldIdLst)} slides)")


if __name__ == "__main__":
    build()
