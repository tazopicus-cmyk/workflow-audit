"""Render audit-pack.pdf from markdown using fpdf2 + DejaVu (same pattern as Tin Dog samples)."""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

from slack_audit_digest.sanitize import assert_no_em_dashes, sanitize_copy

_PKG_ROOT = Path(__file__).resolve().parents[2]
_FONT_DIR = _PKG_ROOT / "fonts"

FONT_CANDIDATES = [
    _FONT_DIR / "DejaVuSans.ttf",
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
]
FONT_B_CANDIDATES = [
    _FONT_DIR / "DejaVuSans-Bold.ttf",
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    Path("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"),
]


def _first_existing(paths: list[Path]) -> Path:
    for path in paths:
        if path.is_file():
            return path
    raise FileNotFoundError(
        "DejaVuSans.ttf not found. Vendor it under slack-audit-digester/fonts/ "
        "or install fonts-dejavu-core."
    )


class AuditPDF(FPDF):
    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("DejaVu", "I", 8)
        self.set_text_color(110)
        self.cell(
            0,
            10,
            f"Tin Dog Digital - Slack Opportunity Audit  |  {self.page_no()}",
            align="C",
        )


def render_pdf(markdown: str, out_path: Path) -> None:
    markdown = sanitize_copy(markdown)
    assert_no_em_dashes(markdown, "audit-pack.pdf source")

    font = _first_existing(FONT_CANDIDATES)
    font_b = _first_existing(FONT_B_CANDIDATES)

    pdf = AuditPDF(format="Letter", unit="pt")
    pdf.set_auto_page_break(auto=True, margin=54)
    pdf.add_font("DejaVu", "", str(font))
    pdf.add_font("DejaVu", "B", str(font_b))
    pdf.add_font("DejaVu", "I", str(font))
    pdf.add_page()
    pdf.set_left_margin(54)
    pdf.set_right_margin(54)
    width = pdf.epw

    for raw in markdown.splitlines():
        line = raw.rstrip()
        if not line:
            pdf.ln(8)
            continue

        if line.startswith("# "):
            pdf.set_font("DejaVu", "B", 18)
            pdf.set_text_color(20)
            pdf.multi_cell(width, 22, _plain(line[2:]))
            pdf.ln(6)
        elif line.startswith("## "):
            pdf.ln(6)
            pdf.set_font("DejaVu", "B", 13)
            pdf.set_text_color(30)
            pdf.multi_cell(width, 18, _plain(line[3:]))
            pdf.ln(2)
        elif line.startswith("### "):
            pdf.set_font("DejaVu", "B", 11)
            pdf.set_text_color(40)
            pdf.multi_cell(width, 15, _plain(line[4:]))
            pdf.ln(2)
        else:
            text = _plain(line)
            if text.startswith("• ") or text.startswith("- "):
                text = "• " + text[2:]
            pdf.set_font("DejaVu", "", 10.5)
            pdf.set_text_color(35)
            x = pdf.get_x()
            if text.startswith("• "):
                pdf.set_x(x + 8)
                pdf.multi_cell(width - 8, 14, text)
            else:
                pdf.multi_cell(width, 14, text)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out_path))
    if out_path.stat().st_size < 200:
        raise RuntimeError(f"PDF too small to be valid: {out_path}")
    header = out_path.read_bytes()[:5]
    if header != b"%PDF-":
        raise RuntimeError(f"PDF missing %PDF- header: {out_path}")


def _plain(text: str) -> str:
    text = text.strip()
    text = text.replace("**", "")
    text = text.replace("__", "")
    return sanitize_copy(text)
