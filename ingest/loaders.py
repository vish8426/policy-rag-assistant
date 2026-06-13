"""Document loaders for the policy corpus.

Each supported file type (.md, .html, .txt, .pdf) is parsed and cleaned into a
common ``Document`` made of ordered ``Section``s. Keeping a heading-aware section
structure lets the chunker produce citation-friendly chunks (each chunk knows the
document title, document ID, and the section it came from).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from bs4 import BeautifulSoup
from pypdf import PdfReader


# ----------------------------- data model -----------------------------

@dataclass
class Section:
    heading: str          # e.g. "2. Health Insurance"  ("Preamble" for content above the first heading)
    text: str             # cleaned section body (no heading line)


@dataclass
class Document:
    doc_id: str           # stable citation key, e.g. "HR-004" (falls back to filename stem)
    title: str            # human title, e.g. "Helix Technologies - Benefits & Compensation Policy"
    source: str           # file name, e.g. "benefits-and-compensation.md"
    fmt: str              # "md" | "html" | "txt" | "pdf"
    sections: List[Section] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n\n".join(s.text for s in self.sections if s.text.strip())


# ----------------------------- helpers -----------------------------

_DOC_ID_RE = re.compile(r"Document\s*ID\s*[:*]*\s*([A-Z]+-\d+)", re.IGNORECASE)
_MD_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
_NUM_HEADING_RE = re.compile(r"^(\d+)\.\s+([A-Z].*\S)\s*$")


def _clean_whitespace(text: str) -> str:
    # Collapse 3+ blank lines, strip trailing spaces, normalize newlines.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _find_doc_id(text: str, fallback: str) -> str:
    m = _DOC_ID_RE.search(text)
    return m.group(1).upper() if m else fallback


def _sectionize_markup(lines: List[str], heading_re: re.Pattern) -> List[Section]:
    """Split a list of text lines into sections on heading lines."""
    sections: List[Section] = []
    cur_heading = "Preamble"
    buf: List[str] = []

    def flush():
        body = _clean_whitespace("\n".join(buf))
        if body:
            sections.append(Section(heading=cur_heading, text=body))

    for line in lines:
        m = heading_re.match(line)
        if m:
            flush()
            buf = []
            # group(2) for md/numbered headings is the heading text
            cur_heading = m.group(2).strip() if m.lastindex and m.lastindex >= 2 else m.group(1).strip()
        else:
            buf.append(line)
    flush()
    return sections


# ----------------------------- per-format loaders -----------------------------

def _load_markdown(path: Path) -> Document:
    raw = _clean_whitespace(path.read_text(encoding="utf-8"))
    lines = raw.split("\n")
    title = path.stem
    for line in lines:
        m = _MD_HEADING_RE.match(line)
        if m and m.group(1) == "#":
            title = m.group(2).strip()
            break
    sections = _sectionize_markup(lines, _MD_HEADING_RE)
    return Document(
        doc_id=_find_doc_id(raw, path.stem),
        title=title,
        source=path.name,
        fmt="md",
        sections=sections,
    )


def _load_html(path: Path) -> Document:
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")

    title = path.stem
    if soup.title and soup.title.get_text(strip=True):
        title = soup.title.get_text(strip=True)
    elif soup.find("h1"):
        title = soup.find("h1").get_text(strip=True)

    # Flatten the body to markdown-like lines so we can reuse the md sectionizer.
    body = soup.body or soup
    lines: List[str] = []
    for el in body.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li"]):
        text = el.get_text(" ", strip=True)
        if not text:
            continue
        if el.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            lines.append(f"## {text}")
        elif el.name == "li":
            lines.append(f"- {text}")
        else:
            lines.append(text)
    full_text = "\n".join(lines)
    sections = _sectionize_markup(lines, _MD_HEADING_RE)
    return Document(
        doc_id=_find_doc_id(full_text, path.stem),
        title=title,
        source=path.name,
        fmt="html",
        sections=sections,
    )


def _load_txt(path: Path) -> Document:
    raw = _clean_whitespace(path.read_text(encoding="utf-8"))
    lines = raw.split("\n")
    # Title = first non-empty line.
    title = next((l.strip() for l in lines if l.strip()), path.stem)

    # Treat ALL-CAPS lines (3+ chars, no lowercase) as section headings; drop "----" rules.
    norm: List[str] = []
    for line in lines:
        s = line.strip()
        if re.fullmatch(r"[-=_]{3,}", s):
            continue
        if s and s.upper() == s and re.search(r"[A-Z]", s) and not re.search(r"[a-z]", s) and len(s) > 3:
            norm.append(f"## {s.title()}")
        else:
            norm.append(line)
    sections = _sectionize_markup(norm, _MD_HEADING_RE)
    return Document(
        doc_id=_find_doc_id(raw, path.stem),
        title=title.title() if title.isupper() else title,
        source=path.name,
        fmt="txt",
        sections=sections,
    )


def _load_pdf(path: Path) -> Document:
    reader = PdfReader(str(path))
    pages = [(p.extract_text() or "") for p in reader.pages]
    raw = _clean_whitespace("\n".join(pages))
    lines = raw.split("\n")

    # Title: PDF metadata title, else first non-empty line.
    title = None
    try:
        if reader.metadata and reader.metadata.title:
            title = str(reader.metadata.title).strip()
    except Exception:
        title = None
    if not title:
        title = next((l.strip() for l in lines if l.strip()), path.stem)

    # Convert "N. Title" numbered headings into markdown headings.
    norm = [f"## {m.group(2)}" if (m := _NUM_HEADING_RE.match(l)) else l for l in lines]
    sections = _sectionize_markup(norm, _MD_HEADING_RE)
    return Document(
        doc_id=_find_doc_id(raw, path.stem),
        title=title,
        source=path.name,
        fmt="pdf",
        sections=sections,
    )


_LOADERS = {
    ".md": _load_markdown,
    ".markdown": _load_markdown,
    ".html": _load_html,
    ".htm": _load_html,
    ".txt": _load_txt,
    ".pdf": _load_pdf,
}

SUPPORTED_EXTENSIONS = tuple(_LOADERS.keys())


def load_file(path: Path) -> Optional[Document]:
    """Load a single file into a Document, or None if the type is unsupported."""
    loader = _LOADERS.get(path.suffix.lower())
    if loader is None:
        return None
    return loader(path)


def load_corpus(corpus_dir: Path) -> List[Document]:
    """Load every supported file in ``corpus_dir`` (sorted for deterministic order)."""
    docs: List[Document] = []
    for path in sorted(corpus_dir.iterdir()):
        if path.is_file() and path.suffix.lower() in _LOADERS:
            doc = load_file(path)
            if doc and doc.sections:
                docs.append(doc)
    return docs
