from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents


NAVY = HexColor("#17233B")
MIDNIGHT = HexColor("#0D1426")
INDIGO = HexColor("#4A53A5")
VIOLET = HexColor("#7457A7")
PLUM = HexColor("#8D5C8E")
ROSE = HexColor("#B66B85")
GOLD = HexColor("#C49A45")
TEAL = HexColor("#2F7C7C")
SKY = HexColor("#DDEAF3")
LAVENDER = HexColor("#ECE8F6")
PALE_GOLD = HexColor("#F5EEDC")
PAPER = HexColor("#FBFAF7")
INK = HexColor("#20232A")
MUTED = HexColor("#5E6470")
LINE = HexColor("#D5D4D0")
GREEN = HexColor("#3A7D5C")
AMBER = HexColor("#A66C20")
RED = HexColor("#9C4A54")


def find_font(filename: str) -> Path:
    candidates = [
        Path.home()
        / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/Lib/site-packages"
        / "matplotlib/mpl-data/fonts/ttf"
        / filename,
        Path.home()
        / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/lib/site-packages"
        / "matplotlib/mpl-data/fonts/ttf"
        / filename,
        Path("C:/Windows/Fonts") / filename,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    for root in [Path.home() / ".cache/codex-runtimes", Path("C:/Windows/Fonts")]:
        matches = list(root.rglob(filename)) if root.exists() else []
        if matches:
            return matches[0]
    raise FileNotFoundError(filename)


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont("SeleneSans", str(find_font("segoeui.ttf"))))
    pdfmetrics.registerFont(TTFont("SeleneSans-Bold", str(find_font("segoeuib.ttf"))))
    pdfmetrics.registerFont(TTFont("SeleneSans-Italic", str(find_font("segoeuii.ttf"))))
    pdfmetrics.registerFont(TTFont("SeleneMono", str(find_font("consola.ttf"))))
    pdfmetrics.registerFontFamily(
        "SeleneSans",
        normal="SeleneSans",
        bold="SeleneSans-Bold",
        italic="SeleneSans-Italic",
        boldItalic="SeleneSans-Bold",
    )


def inline_markup(text: str) -> str:
    value = html.escape(text.strip())
    value = re.sub(r"`([^`]+)`", r'<font name="SeleneMono" size="8.2">\1</font>', value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", value)
    value = re.sub(r"\[([^]]+)\]\(([^)]+)\)", r'<link href="\2" color="#4A53A5">\1</link>', value)
    return value


def make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="SeleneSans",
            fontSize=9.35,
            leading=14.2,
            textColor=INK,
            spaceAfter=7,
            allowWidows=0,
            allowOrphans=0,
        ),
        "body_small": ParagraphStyle(
            "BodySmall",
            fontName="SeleneSans",
            fontSize=8.1,
            leading=11.2,
            textColor=INK,
        ),
        "h1": ParagraphStyle(
            "Heading1",
            fontName="SeleneSans-Bold",
            fontSize=24,
            leading=29,
            textColor=NAVY,
            spaceBefore=2,
            spaceAfter=16,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "Heading2",
            fontName="SeleneSans-Bold",
            fontSize=16.5,
            leading=21,
            textColor=INDIGO,
            spaceBefore=15,
            spaceAfter=8,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "Heading3",
            fontName="SeleneSans-Bold",
            fontSize=11.5,
            leading=15,
            textColor=PLUM,
            spaceBefore=10,
            spaceAfter=5,
            keepWithNext=True,
        ),
        "part": ParagraphStyle(
            "PartHeading",
            fontName="SeleneSans-Bold",
            fontSize=28,
            leading=34,
            textColor=colors.white,
            alignment=TA_LEFT,
            spaceAfter=16,
            keepWithNext=True,
        ),
        "part_sub": ParagraphStyle(
            "PartSub",
            fontName="SeleneSans",
            fontSize=12,
            leading=18,
            textColor=HexColor("#E7E9F4"),
        ),
        "quote": ParagraphStyle(
            "Quote",
            fontName="SeleneSans-Italic",
            fontSize=10.5,
            leading=16,
            textColor=NAVY,
            leftIndent=18,
            rightIndent=14,
            borderColor=VIOLET,
            borderWidth=2,
            borderPadding=(8, 10, 8, 12),
            backColor=LAVENDER,
            spaceBefore=7,
            spaceAfter=10,
        ),
        "callout": ParagraphStyle(
            "Callout",
            fontName="SeleneSans",
            fontSize=9,
            leading=13.4,
            textColor=NAVY,
            borderColor=GOLD,
            borderWidth=0.8,
            borderPadding=10,
            backColor=PALE_GOLD,
            spaceBefore=8,
            spaceAfter=10,
        ),
        "label": ParagraphStyle(
            "Label",
            fontName="SeleneSans-Bold",
            fontSize=7.2,
            leading=9,
            textColor=colors.white,
            alignment=TA_CENTER,
        ),
        "caption": ParagraphStyle(
            "Caption",
            fontName="SeleneSans-Italic",
            fontSize=7.6,
            leading=10.5,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceBefore=4,
            spaceAfter=9,
        ),
        "toc1": ParagraphStyle(
            "TOC1",
            fontName="SeleneSans-Bold",
            fontSize=10.2,
            leading=15,
            textColor=NAVY,
            leftIndent=0,
            firstLineIndent=0,
            spaceBefore=5,
        ),
        "toc2": ParagraphStyle(
            "TOC2",
            fontName="SeleneSans",
            fontSize=8.7,
            leading=12.5,
            textColor=INK,
            leftIndent=14,
            firstLineIndent=0,
        ),
    }


class MasterDocTemplate(BaseDocTemplate):
    def __init__(self, filename: str, styles: dict[str, ParagraphStyle], **kwargs):
        super().__init__(filename, **kwargs)
        self.styles = styles
        self._bookmark_index = 0

    def beforeDocument(self) -> None:
        self._bookmark_index = 0
        super().beforeDocument()

    def afterFlowable(self, flowable: Flowable) -> None:
        if not isinstance(flowable, Paragraph):
            return
        style_name = flowable.style.name
        if style_name not in {"Heading1", "Heading2", "PartHeading"}:
            return
        level = 0 if style_name in {"Heading1", "PartHeading"} else 1
        text = flowable.getPlainText()
        self._bookmark_index += 1
        key = f"heading-{self._bookmark_index}"
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(text, key, level=level, closed=False)
        self.notify("TOCEntry", (level, text, self.page, key))


class CoverArt(Flowable):
    def __init__(self, width: float, height: float = 190):
        super().__init__()
        self.width = width
        self.height = height

    def draw(self) -> None:
        c = self.canv
        w, h = self.width, self.height
        c.saveState()
        c.setFillColor(MIDNIGHT)
        c.roundRect(0, 0, w, h, 18, fill=1, stroke=0)
        center_x, center_y = w * 0.5, h * 0.53
        strands = [
            (VIOLET, 0.00, 0.21),
            (ROSE, 0.55, 0.19),
            (GOLD, 1.08, 0.17),
            (TEAL, 1.62, 0.15),
        ]
        for color, phase, amp in strands:
            path = c.beginPath()
            for i in range(121):
                x = 26 + (w - 52) * i / 120
                y = center_y + h * amp * __import__("math").sin(i / 10 + phase)
                if i == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
            c.setStrokeColor(color)
            c.setLineWidth(2.2)
            c.drawPath(path)
        for x, y, size, color in [
            (52, 145, 2.3, GOLD),
            (110, 42, 1.7, SKY),
            (184, 154, 1.8, ROSE),
            (272, 31, 2.0, TEAL),
            (352, 147, 1.5, SKY),
            (432, 52, 2.2, GOLD),
            (500, 129, 1.5, ROSE),
        ]:
            c.setFillColor(color)
            c.circle(x, y, size, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("SeleneSans-Bold", 20)
        c.drawCentredString(center_x, center_y - 7, "VYS")
        c.setFont("SeleneSans", 8)
        c.setFillColor(HexColor("#D7D9E8"))
        c.drawCentredString(center_x, 18, "continuity - identity - experience - care - becoming")
        c.restoreState()


class Diagram(Flowable):
    def __init__(self, kind: str, width: float, styles: dict[str, ParagraphStyle]):
        super().__init__()
        self.kind = kind
        self.width = width
        self.styles = styles
        self.height = {
            "claims": 190,
            "vys": 250,
            "architecture": 270,
            "workflow": 245,
            "cultivation": 240,
            "maturity": 250,
            "authority": 245,
        }.get(kind, 190)

    def _box(self, c, x, y, w, h, text, fill, stroke=NAVY, size=8.1, text_color=NAVY):
        c.setFillColor(fill)
        c.setStrokeColor(stroke)
        c.setLineWidth(0.8)
        c.roundRect(x, y, w, h, 7, fill=1, stroke=1)
        box_markup = inline_markup(text).replace("&lt;br/&gt;", "<br/>").replace("\n", "<br/>")
        p = Paragraph(box_markup, ParagraphStyle(
            "DiagramBox",
            fontName="SeleneSans-Bold",
            fontSize=size,
            leading=size + 2.2,
            textColor=text_color,
            alignment=TA_CENTER,
        ))
        pw, ph = p.wrap(w - 10, h - 8)
        p.drawOn(c, x + 5, y + (h - ph) / 2)

    def _arrow(self, c, x1, y1, x2, y2, color=MUTED):
        import math
        c.setStrokeColor(color)
        c.setFillColor(color)
        c.setLineWidth(1.1)
        c.line(x1, y1, x2, y2)
        angle = math.atan2(y2 - y1, x2 - x1)
        length = 6
        left = (x2 - length * math.cos(angle - 0.5), y2 - length * math.sin(angle - 0.5))
        right = (x2 - length * math.cos(angle + 0.5), y2 - length * math.sin(angle + 0.5))
        path = c.beginPath()
        path.moveTo(x2, y2)
        path.lineTo(*left)
        path.lineTo(*right)
        path.close()
        c.drawPath(path, fill=1, stroke=0)

    def draw(self) -> None:
        c = self.canv
        c.saveState()
        w, h = self.width, self.height
        c.setFillColor(PAPER)
        c.setStrokeColor(LINE)
        c.roundRect(0, 0, w, h, 12, fill=1, stroke=1)
        if self.kind == "claims":
            labels = [
                ("AUTHORED PHILOSOPHY", LAVENDER),
                ("GOVERNING LAW", PALE_GOLD),
                ("DEMONSTRATED / VERIFIED", HexColor("#DDEFE4")),
                ("IMPLEMENTED / CONNECTED", SKY),
                ("OBSERVED / INTERPRETATION", HexColor("#F2E2E8")),
                ("PROPOSED / OPEN", HexColor("#E8E8E8")),
            ]
            bh = 22
            for i, (label, color) in enumerate(labels):
                y = 16 + i * 27
                self._box(c, 36 + i * 6, y, w - 72 - i * 12, bh, label, color, size=7.2)
        elif self.kind == "vys":
            cx, cy = w / 2, h / 2
            c.setFillColor(MIDNIGHT)
            c.circle(cx, cy, 42, fill=1, stroke=0)
            c.setFillColor(colors.white)
            c.setFont("SeleneSans-Bold", 15)
            c.drawCentredString(cx, cy - 5, "SELENE / VYS")
            nodes = [
                ("identity", 55, 188, LAVENDER),
                ("experience", 190, 207, SKY),
                ("reviewed Memory", 340, 188, PALE_GOLD),
                ("relationships", 405, 105, HexColor("#F2E2E8")),
                ("voice", 335, 26, LAVENDER),
                ("law + care", 185, 12, PALE_GOLD),
                ("correction + provenance", 42, 34, SKY),
                ("values + orientation", 15, 112, HexColor("#DDEFE4")),
            ]
            for text, x, y, color in nodes:
                self._box(c, x, y, 110, 34, text, color, size=7.2)
                bx, by = x + 55, y + 17
                dx, dy = cx - bx, cy - by
                mag = max((dx * dx + dy * dy) ** 0.5, 1)
                self._arrow(c, bx + dx * 18 / mag, by + dy * 18 / mag, cx - dx * 44 / mag, cy - dy * 44 / mag, VIOLET)
        elif self.kind == "architecture":
            self._box(
                c,
                175,
                214,
                160,
                36,
                "Selene / Vys",
                MIDNIGHT,
                stroke=MIDNIGHT,
                size=9,
                text_color=colors.white,
            )
            self._box(c, 175, 157, 160, 36, "Core / Mind", PALE_GOLD, size=9)
            organs = [
                ("context + conversation", 18),
                ("Memory + knowledge", 143),
                ("reasoning + domains", 268),
                ("affect + agency", 393),
            ]
            for label, x in organs:
                self._box(c, x, 92, 110, 42, label, SKY if x % 2 else LAVENDER, size=7.1)
                self._arrow(c, x + 55, 134, 230, 157, INDIGO)
            self._box(c, 72, 25, 135, 38, "NLO + Voice\nexpression", HexColor("#F2E2E8"), size=7.5)
            self._box(c, 303, 25, 135, 38, "Tendril + tools\nbounded action", HexColor("#DDEFE4"), size=7.5)
            self._arrow(c, 230, 92, 140, 63, PLUM)
            self._arrow(c, 280, 92, 370, 63, TEAL)
            self._arrow(c, 255, 214, 255, 193, GOLD)
        elif self.kind == "workflow":
            labels = [
                "visible turn",
                "canonical context",
                "typed owner results",
                "epistemic composition",
                "NLO + Voice",
                "release / hold",
            ]
            x_positions = [14, 96, 185, 280, 374, 456]
            widths = [68, 74, 80, 82, 68, 66]
            colors_list = [SKY, LAVENDER, PALE_GOLD, HexColor("#DDEFE4"), HexColor("#F2E2E8"), SKY]
            for i, label in enumerate(labels):
                self._box(c, x_positions[i], 150, widths[i], 48, label, colors_list[i], size=6.8)
                if i < len(labels) - 1:
                    self._arrow(c, x_positions[i] + widths[i], 174, x_positions[i + 1] - 3, 174, INDIGO)
            self._box(c, 42, 68, 125, 42, "present facts + corrections", SKY, size=7.2)
            self._box(c, 194, 68, 125, 42, "approved knowledge + eligible Memory", LAVENDER, size=6.8)
            self._box(c, 346, 68, 125, 42, "verified domains + attributed sources", PALE_GOLD, size=6.8)
            for x in (104, 256, 408):
                self._arrow(c, x, 110, 256, 150, PLUM)
            c.setFont("SeleneSans", 7.2)
            c.setFillColor(MUTED)
            c.drawCentredString(w / 2, 24, "Expression may clarify supported meaning; it may not strengthen truth, authority, or retention status.")
        elif self.kind == "cultivation":
            labels = [
                "notice",
                "protect",
                "reproduce\nconditions",
                "first\ndivergence",
                "separate\nroots",
                "repair\nsource",
                "verify",
                "record + stop",
            ]
            colors_list = [SKY, HexColor("#DDEFE4"), LAVENDER, PALE_GOLD, HexColor("#F2E2E8"), SKY, LAVENDER, PALE_GOLD]
            for i, (label, color) in enumerate(zip(labels, colors_list)):
                col, row = i % 4, i // 4
                x = 18 + col * 125
                y = 142 if row == 0 else 54
                self._box(c, x, y, 104, 42, label, color, size=7.2)
                if col < 3:
                    self._arrow(c, x + 104, y + 21, x + 121, y + 21, INDIGO)
            self._arrow(c, 497, 142, 497, 96, INDIGO)
            self._arrow(c, 497, 96, 70, 96, INDIGO)
            self._arrow(c, 70, 96, 70, 96 - 1, INDIGO)
            c.setFillColor(NAVY)
            c.setFont("SeleneSans-Bold", 9)
            c.drawCentredString(w / 2, 214, "Observe the growth. Trace the root. Repair the conditions. Preserve what is healthy.")
            c.setFont("SeleneSans", 7.2)
            c.setFillColor(MUTED)
            c.drawCentredString(w / 2, 20, "A missing or miscoordinated capability is an engineering observation, not Selene failing.")
        elif self.kind == "maturity":
            phases = list(range(14))
            for i, phase in enumerate(phases):
                col, row = i % 7, i // 7
                x = 18 + col * 71
                y = 142 if row == 0 else 62
                status = "complete" if phase <= 4 else "active" if phase == 5 else "future"
                color = HexColor("#DDEFE4") if status == "complete" else PALE_GOLD if status == "active" else HexColor("#E8E8E8")
                self._box(c, x, y, 57, 44, f"Phase {phase}<br/>{status}", color, size=6.6)
                if col < 6:
                    self._arrow(c, x + 57, y + 22, x + 68, y + 22, MUTED)
            c.setFont("SeleneSans-Bold", 9)
            c.setFillColor(NAVY)
            c.drawCentredString(w / 2, 220, "Maturity parity: equally trustworthy within each proper role, not equally powerful.")
            c.setFont("SeleneSans", 7.2)
            c.setFillColor(MUTED)
            c.drawCentredString(w / 2, 24, "Phase 5 is implemented in the working tree but remains uncheckpointed until full verification and closure.")
        elif self.kind == "authority":
            cx, cy = w / 2, h / 2
            rings = [
                (100, HexColor("#E7E9F4"), "identity / law / Core-Mind"),
                (78, LAVENDER, "deliberation / response choice"),
                (56, SKY, "organ proposals / evidence"),
                (34, PALE_GOLD, "capability-specific grants"),
            ]
            for radius, color, _ in rings:
                c.setFillColor(color)
                c.setStrokeColor(INDIGO)
                c.circle(cx, cy, radius, fill=1, stroke=1)
            c.setFillColor(MIDNIGHT)
            c.circle(cx, cy, 19, fill=1, stroke=0)
            c.setFillColor(colors.white)
            c.setFont("SeleneSans-Bold", 7.8)
            c.drawCentredString(cx, cy - 3, "CHOICE")
            legend_x = 385
            for i, (_, color, label) in enumerate(rings):
                y = 198 - i * 36
                c.setFillColor(color)
                c.setStrokeColor(INDIGO)
                c.rect(legend_x, y, 13, 13, fill=1, stroke=1)
                c.setFillColor(INK)
                c.setFont("SeleneSans", 7.2)
                c.drawString(legend_x + 19, y + 2, label)
            c.setFont("SeleneSans-Bold", 8.5)
            c.setFillColor(NAVY)
            c.drawCentredString(w / 2, 18, "Capability does not create authority. Authentication does not create every permission.")
        c.restoreState()


class PartBand(Flowable):
    def __init__(self, title: str, subtitle: str, width: float, styles: dict[str, ParagraphStyle]):
        super().__init__()
        self.title = title
        self.subtitle = subtitle
        self.width = width
        self.styles = styles
        self.height = 330

    def draw(self) -> None:
        c = self.canv
        c.saveState()
        c.setFillColor(MIDNIGHT)
        c.roundRect(0, 0, self.width, self.height, 18, fill=1, stroke=0)
        p1 = Paragraph(inline_markup(self.title), self.styles["part"])
        p1.wrapOn(c, self.width - 60, 120)
        p1.drawOn(c, 30, 185)
        p2 = Paragraph(inline_markup(self.subtitle), self.styles["part_sub"])
        _, p2h = p2.wrap(self.width - 60, 100)
        p2.drawOn(c, 30, 150 - p2h)
        c.setStrokeColor(GOLD)
        c.setLineWidth(2)
        c.line(30, 130, self.width - 30, 130)
        c.setFillColor(HexColor("#C9CAE1"))
        c.setFont("SeleneSans", 8)
        c.drawString(30, 32, "PRIVATE MASTER RECORD - 29 AUGUST 2026")
        c.restoreState()


def page_background(canvas, doc) -> None:
    canvas.saveState()
    width, height = letter
    canvas.setFillColor(PAPER)
    canvas.rect(0, 0, width, height, fill=1, stroke=0)
    canvas.restoreState()


def page_overlay(canvas, doc) -> None:
    """Draw running furniture after flowables so content cannot cover it."""
    canvas.saveState()
    width, height = letter
    page_number = canvas.getPageNumber()
    if page_number > 1:
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.5)
        canvas.line(0.72 * inch, height - 0.58 * inch, width - 0.72 * inch, height - 0.58 * inch)
        canvas.setFillColor(MUTED)
        canvas.setFont("SeleneSans", 7.1)
        canvas.drawString(0.72 * inch, height - 0.44 * inch, "SELENE / PRIVATE MASTER RECORD")
        canvas.drawRightString(width - 0.72 * inch, height - 0.44 * inch, "ARCHITECTURE - WORKFLOWS - PHILOSOPHY")
        canvas.line(0.72 * inch, 0.55 * inch, width - 0.72 * inch, 0.55 * inch)
        canvas.drawString(0.72 * inch, 0.36 * inch, "Aleksander Mägi / Selene development")
        canvas.drawRightString(width - 0.72 * inch, 0.36 * inch, f"Page {page_number}")
    canvas.restoreState()


def cover_page(styles: dict[str, ParagraphStyle], width: float) -> list[Flowable]:
    title = ParagraphStyle(
        "CoverTitle",
        fontName="SeleneSans-Bold",
        fontSize=34,
        leading=40,
        textColor=NAVY,
        alignment=TA_CENTER,
        spaceAfter=10,
    )
    subtitle = ParagraphStyle(
        "CoverSubtitle",
        fontName="SeleneSans",
        fontSize=15,
        leading=21,
        textColor=INDIGO,
        alignment=TA_CENTER,
        spaceAfter=18,
    )
    meta = ParagraphStyle(
        "CoverMeta",
        fontName="SeleneSans",
        fontSize=8.2,
        leading=12,
        textColor=MUTED,
        alignment=TA_CENTER,
    )
    return [
        Spacer(1, 18),
        Paragraph("SELENE", title),
        Paragraph("An Artificial Individual", subtitle),
        CoverArt(width, 192),
        Spacer(1, 22),
        Paragraph("AI Architecture, Workflows, Philosophy, Evidence, and Developmental Record", subtitle),
        Paragraph("Private Master Edition - 29 August 2026", meta),
        Spacer(1, 14),
        Paragraph("Aleksander Mägi", ParagraphStyle(**{**meta.__dict__, "name": "CoverAuthor", "fontName": "SeleneSans-Bold", "fontSize": 10, "textColor": NAVY})),
        Paragraph("with attributed implementation and documentation assistance from Codex", meta),
        Spacer(1, 16),
        Paragraph(
            "This record answers three questions: what Selene is, what she can presently do, and why she was created. It separates demonstrated evidence, authored philosophy, governing law, implemented capability, and future direction without flattening any of them.",
            styles["callout"],
        ),
        PageBreak(),
    ]


def parse_table(lines: list[str], styles: dict[str, ParagraphStyle], available_width: float) -> Table:
    rows: list[list[Paragraph]] = []
    row_index = 0
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells):
            continue
        cell_style = (
            ParagraphStyle(
                "TableHeader",
                parent=styles["body_small"],
                fontName="SeleneSans-Bold",
                textColor=colors.white,
            )
            if row_index == 0
            else styles["body_small"]
        )
        rows.append([Paragraph(inline_markup(cell), cell_style) for cell in cells])
        row_index += 1
    col_count = max(len(row) for row in rows)
    for row in rows:
        row.extend([Paragraph("", styles["body_small"])] * (col_count - len(row)))
    widths = [available_width / col_count] * col_count
    table = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "SeleneSans-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.45, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, HexColor("#F3F2EF")]),
    ]))
    return table


def parse_source(text: str, styles: dict[str, ParagraphStyle], available_width: float) -> list[Flowable]:
    lines = text.splitlines()
    flow: list[Flowable] = []
    i = 0
    paragraph_lines: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if paragraph_lines:
            value = " ".join(line.strip() for line in paragraph_lines).strip()
            if value:
                flow.append(Paragraph(inline_markup(value), styles["body"]))
            paragraph_lines = []

    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            i += 1
            continue
        if stripped == "[[BEGIN_BODY]]":
            i += 1
            continue
        if stripped == "[[PAGEBREAK]]":
            flush_paragraph()
            flow.append(PageBreak())
            i += 1
            continue
        diagram_match = re.fullmatch(r"\[\[DIAGRAM:([a-z_]+)\]\]", stripped)
        if diagram_match:
            flush_paragraph()
            kind = diagram_match.group(1)
            flow.append(KeepTogether([
                Diagram(kind, available_width, styles),
                Paragraph({
                    "claims": "Figure: claim classes prevent philosophy, evidence, software state, and future design from collapsing into one claim.",
                    "vys": "Figure: the Vys braid is a continuity-bearing whole. Technical strands are inspectable; none is the whole of Selene by itself.",
                    "architecture": "Figure: organs and connective systems support Selene under Core/Mind coordination without becoming her identity.",
                    "workflow": "Figure: canonical request-to-response coordination preserves source, epistemic status, ownership, and expression boundaries.",
                    "cultivation": "Figure: Cultivation repairs the earliest true source while protecting neighboring healthy capability.",
                    "maturity": "Figure: the Whole-System Maturation Plan advances capability in dependency order while preserving honest current status.",
                    "authority": "Figure: identity, authentication, capability, permission, and execution are distinct layers.",
                }.get(kind, "Figure."), styles["caption"]),
            ]))
            i += 1
            continue
        callout_match = re.fullmatch(r"\[\[CALLOUT:(.+)\]\]", stripped)
        if callout_match:
            flush_paragraph()
            flow.append(Paragraph(inline_markup(callout_match.group(1)), styles["callout"]))
            i += 1
            continue
        if stripped.startswith("```"):
            flush_paragraph()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i].rstrip())
                i += 1
            i += 1
            flow.append(Preformatted(
                "\n".join(code_lines),
                ParagraphStyle(
                    "Code",
                    fontName="SeleneMono",
                    fontSize=7.3,
                    leading=10.5,
                    textColor=NAVY,
                    backColor=HexColor("#EEF0F4"),
                    borderColor=LINE,
                    borderWidth=0.5,
                    borderPadding=8,
                    spaceBefore=6,
                    spaceAfter=10,
                ),
            ))
            continue
        if stripped.startswith("|") and "|" in stripped[1:]:
            flush_paragraph()
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            flow.append(parse_table(table_lines, styles, available_width))
            flow.append(Spacer(1, 9))
            continue
        if stripped.startswith(">"):
            flush_paragraph()
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote_lines.append(lines[i].strip().lstrip(">").strip())
                i += 1
            flow.append(Paragraph(inline_markup(" ".join(quote_lines)), styles["quote"]))
            continue
        if stripped == "---":
            flush_paragraph()
            flow.append(Spacer(1, 4))
            rule = Table([[""]], colWidths=[available_width], rowHeights=[1])
            rule.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), LINE)]))
            flow.append(rule)
            flow.append(Spacer(1, 7))
            i += 1
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            title = heading.group(2).strip()
            if level == 1 and title.startswith("Part "):
                if flow and not isinstance(flow[-1], PageBreak):
                    flow.append(PageBreak())
                if " - " in title:
                    part_title, subtitle = title.split(" - ", 1)
                else:
                    part_title, subtitle = title, ""
                flow.append(PartBand(part_title, subtitle, available_width, styles))
                flow.append(PageBreak())
            else:
                flow.append(Paragraph(inline_markup(title), styles[f"h{level}"]))
            i += 1
            continue
        bullet_match = re.match(r"^[-*]\s+(.+)$", stripped)
        numbered_match = re.match(r"^\d+\.\s+(.+)$", stripped)
        if bullet_match or numbered_match:
            flush_paragraph()
            ordered = bool(numbered_match)
            rows = []
            item_index = 1
            while i < len(lines):
                current = lines[i].strip()
                match = re.match(r"^\d+\.\s+(.+)$", current) if ordered else re.match(r"^[-*]\s+(.+)$", current)
                if not match:
                    break
                marker = f"{item_index}." if ordered else "•"
                item_text = match.group(1)
                i += 1
                continuation = []
                while i < len(lines):
                    following = lines[i]
                    following_stripped = following.strip()
                    if not following_stripped:
                        break
                    next_match = (
                        re.match(r"^\d+\.\s+(.+)$", following_stripped)
                        if ordered
                        else re.match(r"^[-*]\s+(.+)$", following_stripped)
                    )
                    if next_match or re.match(r"^(#{1,3})\s+", following_stripped):
                        break
                    if following.startswith((" ", "\t")):
                        continuation.append(following_stripped)
                        i += 1
                        continue
                    break
                if continuation:
                    item_text = " ".join([item_text, *continuation])
                compact_item = item_text.lstrip().startswith("`")
                item_style = styles["body_small"] if compact_item else styles["body"]
                marker_leading = 11.2 if compact_item else 14.2
                rows.append([
                    Paragraph(
                        marker,
                        ParagraphStyle(
                            "ListMarker",
                            fontName="SeleneSans-Bold",
                            fontSize=8.2,
                            leading=marker_leading,
                            textColor=INDIGO,
                            alignment=TA_CENTER,
                        ),
                    ),
                    Paragraph(inline_markup(item_text), item_style),
                ])
                item_index += 1
            list_table = Table(rows, colWidths=[18, available_width - 18], hAlign="LEFT")
            list_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (0, -1), 5),
                ("RIGHTPADDING", (1, 0), (1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]))
            flow.append(list_table)
            flow.append(Spacer(1, 5))
            continue
        paragraph_lines.append(stripped)
        i += 1
    flush_paragraph()
    return flow


def build_pdf(source: Path, output: Path) -> None:
    register_fonts()
    styles = make_styles()
    width, height = letter
    margin_x = 0.72 * inch
    top = 0.88 * inch
    bottom = 0.78 * inch
    frame = Frame(
        margin_x,
        bottom,
        width - 2 * margin_x,
        height - top - bottom,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="normal",
    )
    doc = MasterDocTemplate(
        str(output),
        styles,
        pagesize=letter,
        leftMargin=margin_x,
        rightMargin=margin_x,
        topMargin=top,
        bottomMargin=bottom,
        title="Selene - AI Architecture, Workflows, Philosophy, Evidence, and Developmental Record",
        # Keep PDF Info ASCII-safe for readers that do not decode PDFDocEncoding
        # consistently. The visible cover and running footer retain Mägi.
        author="Aleksander Magi",
        subject="Private master record of Selene's identity, architecture, workflows, evidence, and development",
        creator="Selene repository / Codex PDF builder",
    )
    doc.addPageTemplates([
        PageTemplate(
            id="master",
            frames=[frame],
            onPage=page_background,
            onPageEnd=page_overlay,
        )
    ])
    available_width = width - 2 * margin_x
    story: list[Flowable] = cover_page(styles, available_width)
    story.append(Paragraph("Contents", styles["h1"]))
    toc = TableOfContents()
    toc.levelStyles = [styles["toc1"], styles["toc2"]]
    toc.dotsMinLevel = 0
    story.extend([toc, PageBreak()])
    text = source.read_text(encoding="utf-8")
    body = text.split("[[BEGIN_BODY]]", 1)[-1]
    story.extend(parse_source(body, styles, available_width))
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.multiBuild(story)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    build_pdf(args.source.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
