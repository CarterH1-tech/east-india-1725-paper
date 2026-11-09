#!/usr/bin/env python3
"""Build paper.md into paper.pdf using ReportLab.

Usage:
    python build.py [input.md] [output.pdf]

Defaults: paper.md -> paper.pdf
Requires: reportlab  (pip install -r requirements.txt)

This script implements a small Markdown subset:
  # / ## headings, **bold**, *italic*, [text](url), plain URLs,
  numbered/bulleted lists, horizontal breaks, paragraphs.
It uses Arial (Windows) if present for wide Unicode coverage
(£, ƒ, —), otherwise falls back to Helvetica.
"""
import html
import re
import sys
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
    KeepTogether,
)


def register_fonts():
    """Register Arial family if available, else use Helvetica."""
    candidates = {
        "Arial": r"C:\Windows\Fonts\arial.ttf",
        "Arial-Bold": r"C:\Windows\Fonts\arialbd.ttf",
        "Arial-Italic": r"C:\Windows\Fonts\ariali.ttf",
        "Arial-BoldItalic": r"C:\Windows\Fonts\arialbi.ttf",
    }
    # Also try Linux/macOS paths (harmless if absent)
    linux = "/usr/share/fonts/truetype/dejavu/"
    if not Path(candidates["Arial"]).exists():
        # Try DejaVu as metric-compatible substitute
        pairs = [("Arial", linux + "DejaVuSans.ttf"),
                 ("Arial-Bold", linux + "DejaVuSans-Bold.ttf"),
                 ("Arial-Italic", linux + "DejaVuSans-Oblique.ttf"),
                 ("Arial-BoldItalic", linux + "DejaVuSans-BoldOblique.ttf")]
        for name, path in pairs:
            if Path(path).exists():
                try:
                    pdfmetrics.registerFont(TTFont(name, path))
                except Exception:
                    pass
        return "Arial" if "Arial" in pdfmetrics.getRegisteredFontNames() else "Helvetica"
    for name, path in candidates.items():
        try:
            pdfmetrics.registerFont(TTFont(name, path))
        except Exception:
            pass
    pdfmetrics.registerFontFamily(
        "Arial",
        normal="Arial",
        bold="Arial-Bold",
        italic="Arial-Italic",
        boldItalic="Arial-BoldItalic",
    )
    return "Arial"


MD_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
PLAIN_URL = re.compile(r"https?://[^\s<>\]]+")
BOLD = re.compile(r"\*\*([^*]+)\*\*")
ITALIC = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")


def md_to_reportlab_inline(text: str) -> str:
    """Convert inline Markdown to ReportLab Paragraph markup.

    Order matters: escape HTML first, then restore markup.
    """
    # Escape, but preserve URLs for later linking step
    # We escape everything, then unescape our markers.
    text = html.escape(text, quote=False)
    # Markdown links (now HTML-escaped, but []() remain)
    def link_repl(m):
        label = m.group(1)
        url = m.group(2)
        # Keep &amp; in href so ReportLab XML parser accepts it
        return f'<a href="{url}" color="#0645AD">{label}</a>'
    text = MD_LINK.sub(link_repl, text)
    # Bold / italic (asterisks survive HTML escape)
    text = BOLD.sub(r"<b>\1</b>", text)
    text = ITALIC.sub(r"<i>\1</i>", text)
    # Plain URLs not already inside <a ...>...</a> — wrap remaining.
    # Trim trailing sentence punctuation from the URL itself.
    def plain_repl(m):
        url = m.group(0)
        trailing = ""
        while url and url[-1] in ".,;)":
            trailing = url[-1] + trailing
            url = url[:-1]
        return f'<a href="{url}" color="#0645AD">{url}</a>{trailing}'
    # Protect already-created <a>...</a> elements from re-wrapping.
    # (href="..." values must not be treated as plain URLs.)
    parts = re.split(r'(<a[^>]*>.*?</a>)', text, flags=re.DOTALL)
    for i, part in enumerate(parts):
        if not part.startswith("<a"):
            parts[i] = PLAIN_URL.sub(plain_repl, part)
    text = "".join(parts)
    return text


def parse_markdown(md_text: str):
    """Yield (kind, content) blocks. kind in: title, h2, h3, para, list, hr."""
    lines = md_text.splitlines()
    i = 0
    # Buffer for paragraph
    para = []
    blocks = []

    def flush_para():
        if para:
            blocks.append(("para", " ".join(para).strip()))
            para.clear()

    for raw in lines:
        line = raw.strip()
        if not line:
            flush_para()
            continue
        if line.startswith("# "):
            flush_para()
            blocks.append(("title", line[2:].strip()))
        elif line.startswith("## "):
            flush_para()
            blocks.append(("h2", line[3:].strip()))
        elif line.startswith("### "):
            flush_para()
            blocks.append(("h3", line[4:].strip()))
        elif line in ("---", "***", "___"):
            flush_para()
            blocks.append(("hr", ""))
        elif re.match(r"^\d+\.\s+", line) or line.startswith("- ") or line.startswith("* "):
            flush_para()
            # collect consecutive list items as one block each
            blocks.append(("list", line))
        else:
            para.append(line)
    flush_para()
    return blocks


def build(input_path: Path, output_path: Path):
    md_text = input_path.read_text(encoding="utf-8")
    font = register_fonts()
    use_ar = font == "Arial"
    body_font = "Arial" if use_ar else "Helvetica"
    bold_font = "Arial-Bold" if use_ar else "Helvetica-Bold"

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle", parent=styles["Title"],
        fontName=bold_font, fontSize=19, leading=24,
        spaceAfter=10, alignment=1,  # center
        textColor=HexColor("#111111"),
    )
    h2_style = ParagraphStyle(
        "CustomH2", parent=styles["Heading2"],
        fontName=bold_font, fontSize=13, leading=16,
        spaceBefore=14, spaceAfter=7,
        textColor=HexColor("#111111"),
    )
    h3_style = ParagraphStyle(
        "CustomH3", parent=styles["Heading3"],
        fontName=bold_font, fontSize=11, leading=14,
        spaceBefore=10, spaceAfter=5,
    )
    body_style = ParagraphStyle(
        "CustomBody", parent=styles["Normal"],
        fontName=body_font, fontSize=10.2, leading=14.5,
        spaceAfter=8, alignment=4,  # justify
    )
    list_style = ParagraphStyle(
        "CustomList", parent=body_style,
        fontSize=8.8, leading=12.2,
        leftIndent=14, firstLineIndent=0,
        spaceAfter=5, alignment=0,
        wordWrap="CJK",  # allow breaking long URLs
    )
    small_style = ParagraphStyle(
        "CustomSmall", parent=body_style,
        fontSize=9.2, leading=13,
        spaceAfter=6,
    )

    def header_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont(body_font, 7.5)
        canvas.setFillColor(HexColor("#666666"))
        canvas.drawCentredString(
            A4[0] / 2, 12 * mm,
            f"Investing in the East Indies 1725-1750  —  page {doc.page}",
        )
        canvas.drawRightString(
            A4[0] - 18 * mm, 12 * mm, "paper.pdf",
        )
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=18 * mm, bottomMargin=16 * mm,
        title="Investing in the East Indies 1725-1750",
        author="Muse Ember",
    )

    blocks = parse_markdown(md_text)
    story = []
    in_bibliography = False
    for kind, content in blocks:
        if kind == "title":
            story.append(Paragraph(md_to_reportlab_inline(content), title_style))
            story.append(Spacer(1, 4))
        elif kind == "h2":
            if content.strip().lower() == "bibliography":
                in_bibliography = True
            story.append(Paragraph(md_to_reportlab_inline(content), h2_style))
        elif kind == "h3":
            story.append(Paragraph(md_to_reportlab_inline(content), h3_style))
        elif kind == "hr":
            story.append(HRFlowable(width="100%", thickness=0.6, spaceAfter=8, spaceBefore=4))
        elif kind == "list":
            # strip list marker for rendering, keep number for bibliography
            m_num = re.match(r"^(\d+)\.\s+(.*)$", content)
            if m_num:
                num, text = m_num.group(1), m_num.group(2)
                item = f"{num}. {text}"
            else:
                item = re.sub(r"^[-*]\s+", "", content)
                item = "•  " + item
            style = list_style if in_bibliography else body_style
            story.append(Paragraph(md_to_reportlab_inline(item), style))
        elif kind == "para":
            # Detect word-count line to style as small italic-ish
            if content.startswith("Word count:"):
                story.append(Paragraph(md_to_reportlab_inline(content), small_style))
                story.append(Spacer(1, 4))
            else:
                style = small_style if in_bibliography else body_style
                # Bibliography lead-ins like "**Primary...**" are paragraphs
                story.append(Paragraph(md_to_reportlab_inline(content), style))

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"Built {output_path} ({output_path.stat().st_size} bytes) from {input_path}")
    return output_path


if __name__ == "__main__":
    inp = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("paper.md")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("paper.pdf")
    if not inp.exists():
        print(f"Input not found: {inp}", file=sys.stderr)
        sys.exit(1)
    build(inp, out)
