# Investing in the East Indies 1725–1750

Research paper comparing the British East India Company (EIC) and the
Dutch Vereenigde Oostindische Compagnie (VOC) for a January 1725 investor
who must exit in 1745–1750.

- **Paper (Markdown):** `paper.md` — 1,438 words (excluding bibliography),
  with linked bibliography (14 sources: 7 primary, 5 in non-English
  languages — Dutch, French, Portuguese — 7 secondary).
- **PDF build:** `build.py` (ReportLab) + `Makefile`.

## Build the PDF

```bash
pip install -r requirements.txt
python build.py paper.md paper.pdf
# or, on Unix with make:
make pdf
```

Windows (Python launcher):

```powershell
py -m pip install -r requirements.txt
py build.py paper.md paper.pdf
```

Output: `paper.pdf` (A4, with clickable bibliography links).

Optional Pandoc alternative (requires Pandoc + a PDF engine):

```bash
pandoc paper.md -o paper.pdf --pdf-engine=wkhtmltopdf
```

## Contents

- `paper.md` — the paper + word count + linked bibliography
- `build.py` — Markdown → PDF builder
- `Makefile` — `pdf`, `install`, `clean`, `check` targets
- `requirements.txt` — Python dependencies
- `final_paper.md` — same paper (pre-link revision, kept for provenance)
- `draft.txt`, `sources.txt`, `summaries.txt` — research notes
