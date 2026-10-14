# -*- coding: utf-8 -*-
"""Feuille de style "template Canva" pour la présentation PowerPoint.

Fournit palette, primitives de dessin, composants (cartes, KPI, figures,
timeline) et helpers de mise en page. Utilisé par make_pptx.py.
"""

from pathlib import Path

from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

# --- Palette (thème "Green Energy Forms of Power") -------------------------
DARK = RGBColor(0x0B, 0x3B, 0x2E)
DARK2 = RGBColor(0x17, 0x69, 0x4B)
INK = RGBColor(0x0C, 0x2B, 0x22)
BLUE = RGBColor(0x14, 0x85, 0x5A)
TEAL = RGBColor(0x34, 0xC0, 0x8A)
CORAL = RGBColor(0xE2, 0x70, 0x3A)
AMBER = RGBColor(0xE9, 0xB8, 0x24)
VIOLET = RGBColor(0x0F, 0x7C, 0x6C)
SLATE = RGBColor(0x4C, 0x66, 0x59)
MUTED = RGBColor(0x87, 0xA0, 0x92)
LINE = RGBColor(0xDC, 0xE8, 0xDE)
BG = RGBColor(0xF4, 0xF8, 0xF3)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

BLUE_T = RGBColor(0xE4, 0xF3, 0xEC)
TEAL_T = RGBColor(0xE2, 0xF7, 0xEF)
CORAL_T = RGBColor(0xFB, 0xED, 0xE7)
AMBER_T = RGBColor(0xFC, 0xF4, 0xDC)
VIOLET_T = RGBColor(0xE3, 0xF2, 0xF0)

HEAD = "Bahnschrift"
BODY = "Segoe UI"

# --- Géométrie -------------------------------------------------------------
SW = Inches(13.333)
SH = Inches(7.5)
MARGIN = Inches(0.7)
CW = SW - 2 * MARGIN

FIG = None  # défini par l'appelant via set_paths


def set_paths(fig_dir, dash_dir, root_dir):
    global FIG, DASH, ROOT
    FIG, DASH, ROOT = Path(fig_dir), Path(dash_dir), Path(root_dir)


# --- XML helpers -----------------------------------------------------------
def _alpha(shape, pct):
    sf = shape._element.spPr.find(qn("a:solidFill"))
    if sf is None:
        return
    srgb = sf.find(qn("a:srgbClr"))
    if srgb is None:
        return
    srgb.append(srgb.makeelement(qn("a:alpha"), {"val": str(int(pct * 1000))}))


def _spacing(run, pts):
    run._r.get_or_add_rPr().set("spc", str(int(pts * 100)))


# --- Primitives ------------------------------------------------------------
def rect(slide, x, y, w, h, color, line=None, radius=None,
         shape=MSO_SHAPE.RECTANGLE, alpha=None):
    shp = slide.shapes.add_shape(shape, int(x), int(y), int(w), int(h))
    shp.fill.solid()
    shp.fill.fore_color.rgb = color
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(1)
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            shp.adjustments[0] = radius
        except Exception:
            pass
    shp.shadow.inherit = False
    if alpha is not None:
        _alpha(shp, alpha)
    return shp


def rrect(slide, x, y, w, h, color=WHITE, line=None, radius=0.1, alpha=None):
    return rect(slide, x, y, w, h, color, line=line, radius=radius,
                shape=MSO_SHAPE.ROUNDED_RECTANGLE, alpha=alpha)


def circle(slide, x, y, d, color, alpha=None):
    return rect(slide, x, y, d, d, color, shape=MSO_SHAPE.OVAL, alpha=alpha)


def gradient(slide, c1, c2, angle=40.0):
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, int(SW), int(SH))
    try:
        shp.fill.gradient()
        shp.fill.gradient_angle = angle
        st = shp.fill.gradient_stops
        st[0].color.rgb = c1
        st[0].position = 0.0
        st[1].color.rgb = c2
        st[1].position = 1.0
    except Exception:
        shp.fill.solid()
        shp.fill.fore_color.rgb = c1
    shp.line.fill.background()
    shp.shadow.inherit = False
    return shp


def _emit(p, text, size, color, bold, font, ls):
    for i, part in enumerate(text.split("**")):
        if part == "":
            continue
        r = p.add_run()
        r.text = part
        r.font.size = Pt(size)
        r.font.bold = bold or (i % 2 == 1)
        r.font.color.rgb = color
        r.font.name = font
        if ls:
            _spacing(r, ls)


def textbox(slide, x, y, w, h, text, size=16, color=INK, bold=False,
            align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.0,
            font=BODY, ls=0):
    tb = slide.shapes.add_textbox(int(x), int(y), int(w), int(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, ln in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        _emit(p, ln, size, color, bold, font, ls)
    return tb


# --- Chrome ----------------------------------------------------------------
def bg_light(slide):
    rect(slide, 0, 0, SW, SH, BG)


def dots(slide, x, y, cols, rows, gap, d, color, alpha=None):
    for r in range(rows):
        for c in range(cols):
            circle(slide, x + c * gap, y + r * gap, d, color, alpha=alpha)


def footer(slide, num, dark=False):
    col = RGBColor(0x7E, 0x8C, 0xB8) if dark else RGBColor(0x9A, 0xA6, 0xC0)
    bar = RGBColor(0x2A, 0x38, 0x66) if dark else RGBColor(0xE5, 0xE9, 0xF2)
    rect(slide, MARGIN, SH - Inches(0.52), CW, Pt(0.75), bar)
    textbox(slide, MARGIN, SH - Inches(0.44), Inches(9.5), Inches(0.3),
            "SÉRIES TEMPORELLES  ·  ÉNERGIE ALLEMAGNE (ENTSO-E)  ·  R & PYTHON",
            size=8.5, color=col, ls=1.2)
    cx = SW - MARGIN - Inches(0.34)
    circle(slide, cx, SH - Inches(0.55), Inches(0.38),
           RGBColor(0x2A, 0x38, 0x66) if dark else BLUE)
    textbox(slide, cx, SH - Inches(0.55), Inches(0.38), Inches(0.38),
            f"{num:02d}", size=10, color=WHITE, bold=True,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)


def chrome(slide, eyebrow, title, num, accent=BLUE, title_size=29):
    bg_light(slide)
    circle(slide, SW - Inches(1.7), -Inches(2.2), Inches(4.6), accent, alpha=8)
    dots(slide, MARGIN, SH - Inches(1.55), 6, 3, Inches(0.15), Inches(0.045),
         accent, alpha=22)
    textbox(slide, MARGIN, Inches(0.5), CW, Inches(0.3), eyebrow, size=11,
            color=accent, bold=True, ls=2.4)
    textbox(slide, MARGIN, Inches(0.8), CW, Inches(0.8), title, size=title_size,
            color=INK, bold=True, font=HEAD)
    rect(slide, MARGIN, Inches(1.58), Inches(0.66), Inches(0.075), accent)
    footer(slide, num)


def keybar(slide, text, accent=BLUE):
    y = SH - Inches(1.14)
    rrect(slide, MARGIN, y, CW, Inches(0.62), color=accent, alpha=9, radius=0.3)
    rect(slide, MARGIN + Inches(0.2), y + Inches(0.18), Inches(0.075),
         Inches(0.26), accent)
    textbox(slide, MARGIN + Inches(0.44), y, CW - Inches(0.7), Inches(0.62),
            "À RETENIR  ·  " + text, size=11.5, color=INK,
            anchor=MSO_ANCHOR.MIDDLE)


def bullet_list(slide, items, x, y, w, size=14.5, accent=BLUE):
    tb = slide.shapes.add_textbox(int(x), int(y), int(w), int(SH - y))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(10)
        p.line_spacing = 1.08
        rb = p.add_run()
        rb.text = "▸ "
        rb.font.size = Pt(13)
        rb.font.color.rgb = accent
        rb.font.name = BODY
        for j, part in enumerate(it.split("**")):
            if part == "":
                continue
            r = p.add_run()
            r.text = part
            r.font.size = Pt(size)
            r.font.bold = (j % 2 == 1)
            r.font.color.rgb = INK if (j % 2 == 1) else SLATE
            r.font.name = BODY


# --- Composants ------------------------------------------------------------
def stat_card(slide, x, y, w, h, value, label, tint, accent):
    rrect(slide, x, y, w, h, color=tint, radius=0.14)
    rrect(slide, x + Inches(0.28), y + Inches(0.28), Inches(0.44), Inches(0.08),
          color=accent, radius=0.5)
    textbox(slide, x + Inches(0.28), y + Inches(0.5), w - Inches(0.5),
            Inches(0.7), value, size=29, color=accent, bold=True, font=HEAD)
    textbox(slide, x + Inches(0.28), y + h - Inches(0.9), w - Inches(0.5),
            Inches(0.7), label, size=9.5, color=SLATE, ls=1.1)


def icon_card(slide, x, y, w, h, glyph, title, body, accent, tint,
              body_size=11.5):
    rrect(slide, x, y, w, h, color=WHITE, line=LINE, radius=0.12)
    circle(slide, x + Inches(0.3), y + Inches(0.28), Inches(0.62), tint)
    textbox(slide, x + Inches(0.3), y + Inches(0.28), Inches(0.62), Inches(0.62),
            glyph, size=22, color=accent, bold=True, align=PP_ALIGN.CENTER,
            anchor=MSO_ANCHOR.MIDDLE)
    textbox(slide, x + Inches(0.3), y + Inches(1.06), w - Inches(0.6),
            Inches(0.5), title, size=14, color=INK, bold=True, font=HEAD)
    textbox(slide, x + Inches(0.3), y + Inches(1.56), w - Inches(0.6),
            h - Inches(1.76), body, size=body_size, color=SLATE, spacing=1.12)


def cards_grid(slide, items, x, y, w, h, cols=3, tints=None, accents=None):
    n = len(items)
    rows = (n + cols - 1) // cols
    gap = Inches(0.28)
    cw = int((w - gap * (cols - 1)) / cols)
    ch = int((h - gap * (rows - 1)) / rows)
    tints = tints or [BLUE_T]
    accents = accents or [BLUE]
    for i, (glyph, title, body) in enumerate(items):
        r, c = divmod(i, cols)
        icon_card(slide, x + c * (cw + gap), y + r * (ch + gap), cw, ch,
                  glyph, title, body, accents[i % len(accents)],
                  tints[i % len(tints)])


# --- Figures ---------------------------------------------------------------
def _imgsize(path):
    try:
        from PIL import Image
        with Image.open(path) as im:
            return im.size
    except Exception:
        return None


def resolve(fname):
    p = Path(fname)
    if p.is_absolute() and p.exists():
        return p
    for folder in (FIG, DASH, ROOT):
        cand = Path(folder) / fname
        if cand.exists():
            return cand
    return None


def place_image(slide, fname, left, top, max_w, max_h):
    path = resolve(fname)
    if path is None:
        textbox(slide, left, top, max_w, max_h, f"[Figure : {fname}]", size=11,
                color=MUTED, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        return None
    size = _imgsize(path)
    if size:
        ar = size[0] / size[1]
        w, h = int(max_w), int(max_w / ar)
        if h > max_h:
            h, w = int(max_h), int(max_h * ar)
        x = int(left + (max_w - w) / 2)
        y = int(top + (max_h - h) / 2)
        return slide.shapes.add_picture(str(path), x, y, width=w, height=h)
    return slide.shapes.add_picture(str(path), int(left), int(top), width=int(max_w))


def figure(slide, image, x, y, w, h, caption=None, accent=BLUE):
    rrect(slide, x + Inches(0.13), y + Inches(0.13), w, h, color=accent,
          radius=0.05, alpha=18)
    rrect(slide, x, y, w, h, color=WHITE, line=LINE, radius=0.05)
    pad = Inches(0.16)
    ch = Inches(0.36) if caption else 0
    place_image(slide, image, x + pad, y + pad, w - 2 * pad, h - 2 * pad - ch)
    if caption:
        textbox(slide, x + pad, y + h - ch, w - 2 * pad, ch, caption, size=9.5,
                color=MUTED, align=PP_ALIGN.CENTER)


# --- Notes -----------------------------------------------------------------
def note(slide, text):
    slide.notes_slide.notes_text_frame.text = text
