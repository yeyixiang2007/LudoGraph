#!/usr/bin/env python3
"""Convert the LUDO-9 literature review Markdown into LuaLaTeX-ready LaTeX body."""
import re
from pathlib import Path

SRC = Path(__file__).resolve().parent / "literature-review-ludograph.md"
DST = Path(__file__).resolve().parent / "_body.tex"

def esc(s):
    """Escape LaTeX special characters, preserving already-inserted commands."""
    out = []
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c == "\\":
            # keep existing command sequence untouched
            j = i + 1
            while j < n and (s[j].isalpha() or s[j] in "*"):
                j += 1
            out.append(s[i:j])
            i = j
            continue
        if c in "&%$#_{}":
            out.append("\\" + c)
        elif c == "~":
            out.append("\\textasciitilde{}")
        elif c == "^":
            out.append("\\textasciicircum{}")
        else:
            out.append(c)
        i += 1
    return "".join(out)

# Symbols absent from the CJK font. They are routed to math mode, otherwise
# LuaTeX silently drops the glyph (Droid Sans Fallback has no such codepoints).
MATHMAP = {
    "\u2200": "\\forall ",
    "\u2203": "\\exists ",
    "\u2208": "\\in ",
    "\u2209": "\\notin ",
    "\u2260": "\\neq ",
    "\u2264": "\\leq ",
    "\u2265": "\\geq ",
    "\u2227": "\\wedge ",
    "\u2228": "\\vee ",
    "\u2192": "\\rightarrow ",
    "\u2190": "\\leftarrow ",
    "\u2194": "\\leftrightarrow ",
    "\u21d2": "\\Rightarrow ",
    "\u2212": "-",
    "\u03a3": "\\Sigma ",
    "\u03c0": "\\pi ",
    "\u00d7": "\\times ",
    "\u2248": "\\approx ",
    "\u2261": "\\equiv ",
    "\u2205": "\\emptyset ",
    "\u222a": "\\cup ",
    "\u2229": "\\cap ",
    "\u2286": "\\subseteq ",
    "\u00ac": "\\neg ",
}

_SYM_RE = re.compile("([" + "".join(re.escape(k) for k in MATHMAP) + "])")


def map_symbols(text):
    """Wrap CJK-font-absent symbols in math mode so they are not dropped."""
    return "".join(
        "$" + MATHMAP[c] + "$" if c in MATHMAP else c
        for c in _SYM_RE.split(text)
    )


def apply_typography(text):
    """Quote / dash / ellipsis substitutions shared by prose and code spans."""
    text = text.replace("\u201c", "\\textquotedblleft{}")
    text = text.replace("\u201d", "\\textquotedblright{}")
    text = text.replace("\u2018", "\\textquoteleft{}")
    text = text.replace("\u2019", "\\textquoteright{}")
    # ASCII double quotes alternate open/close; Droid Sans Fallback has no
    # straight-quote glyph, so map them to explicit TeX quote macros.
    parts = text.split('"')
    if len(parts) > 1:
        rebuilt = [parts[0]]
        for k, seg in enumerate(parts[1:]):
            rebuilt.append(
                "\\textquotedblleft{}" if k % 2 == 0 else "\\textquotedblright{}"
            )
            rebuilt.append(seg)
        text = "".join(rebuilt)
    text = text.replace("\u2014", "---")
    text = text.replace("\u2013", "--")
    text = text.replace("\u2026", "\\ldots{}")
    return text


def inline(text):
    """Apply inline Markdown -> LaTeX conversions.

    Strategy: stash every construct whose body must NOT be escaped on its own
    (code spans), escape the remaining plain text, then restore stashed bodies
    with their own escaping. Emphasis/link markers are ASCII and survive esc().
    """
    # 1) protect code spans (their content is escaped separately on restore)
    codes = []
    def stash(m):
        codes.append(m.group(1))
        return f"\x00CODE{len(codes) - 1}\x00"
    text = re.sub(r"`([^`]+)`", stash, text)

    # 2) escape LaTeX specials in the remaining plain text
    text = esc(text)

    # 3) apply markdown emphasis / links (markers are ASCII, unaffected by esc)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\\textbf{\1}", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\\emph{\1}", text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
                  r"\\href{\2}{\1}", text)
    text = re.sub(r"<(https?://[^>\s]+)>", r"\\url{\1}", text)

    # smart quotes / dashes / symbols: needed in prose and inside code spans
    text = apply_typography(text)
    text = map_symbols(text)

    # restore code spans as \texttt (typography applies inside them too, since
    # tables and constraint snippets contain CJK-absent symbols)
    def unstash(m):
        idx = int(m.group(1))
        if idx >= len(codes):
            return ""
        body = map_symbols(apply_typography(esc(codes[idx])))
        return "\\texttt{" + body + "}"
    text = re.sub(r"\x00CODE(\d+)\x00", unstash, text)
    return text

def emit_table(lines, out):
    rows = []
    for ln in lines:
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        rows.append(cells)
    # drop the separator row (---)
    body = [r for r in rows if not all(re.fullmatch(r":?-{2,}:?", c or "-") for c in r)]
    if not body:
        return
    ncol = max(len(r) for r in body)
    spec = f"p{{{(0.94 / ncol):.2f}\\textwidth}}"
    colspec = "|".join([spec] * ncol)
    out.append(f"\\begin{{longtable}}{{{colspec}}}")
    out.append("\\hline")
    for idx, r in enumerate(body):
        r = r + [""] * (ncol - len(r))
        cells = [inline(c).replace("|", "\\textbar{}") for c in r]
        out.append(" & ".join(cells) + " \\\\")
        out.append("\\hline")
        if idx == 0:
            out.append("\\endhead")
    out.append("\\end{longtable}")
    out.append("")

def main():
    if not SRC.is_file():
        raise SystemExit(f"missing input: {SRC}")
    text = SRC.read_text(encoding="utf-8")

    lines = text.split("\n")
    out = []
    i = 0
    in_code = False
    code_buf = []
    in_list = None  # 'itemize' or 'enumerate'
    list_depth = 0

    def close_list():
        nonlocal in_list, list_depth
        while list_depth > 0 and in_list is not None:
            out.append(f"\\end{{{in_list}}}")
            list_depth -= 1
        in_list = None

    while i < len(lines):
        ln = lines[i]

        # fenced code blocks
        if ln.strip().startswith("```"):
            if not in_code:
                in_code = True
                code_buf = []
            else:
                in_code = False
                out.append("\\begin{quote}\\begin{verbatim}")
                out.extend(code_buf)
                out.append("\\end{verbatim}\\end{quote}")
            i += 1
            continue
        if in_code:
            code_buf.append(ln)
            i += 1
            continue

        stripped = ln.strip()

        # tables
        if stripped.startswith("|"):
            tbl = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                tbl.append(lines[i])
                i += 1
            close_list()
            emit_table(tbl, out)
            continue

        # headings
        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            close_list()
            level = len(m.group(1))
            # The Markdown headings carry editorial numbers (e.g. "## 1.")
            # while LaTeX numbers sections automatically. Strip the prefix to
            # avoid duplicated or drifting numbers in the rendered document.
            raw_title = re.sub(r"^(?:\d+(?:\.\d+)*\.?|[一二三四五六七八九十]+、)\s*", "", m.group(2))
            title = inline(raw_title)
            if level == 1:
                out.append(f"\\title{{{title}}}")
                out.append("\\maketitle")
                out.append("\\thispagestyle{empty}")
                out.append("\\newpage")
            elif level == 2:
                out.append(f"\\section{{{title}}}")
            elif level == 3:
                out.append(f"\\subsection{{{title}}}")
            else:
                out.append(f"\\subsubsection{{{title}}}")
            i += 1
            continue

        # horizontal rule
        if re.fullmatch(r"-{3,}", stripped):
            i += 1
            continue

        # blockquote (doc metadata)
        if stripped.startswith(">"):
            close_list()
            q = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                q.append(inline(lines[i].strip()[1:].strip()))
                i += 1
            out.append("\\begin{quote}\\small")
            out.append(" \\\\\n".join(x for x in q if x))
            out.append("\\end{quote}")
            continue

        # lists
        m_ul = re.match(r"^(\s*)[-*]\s+(.*)$", ln)
        m_ol = re.match(r"^(\s*)\d+\.\s+(.*)$", ln)
        match = m_ul or m_ol
        if match is not None:
            content = match.group(2)
            want = "itemize" if m_ul is not None else "enumerate"
            if in_list != want:
                close_list()
                in_list = want
                out.append(f"\\begin{{{want}}}")
                list_depth = 1
            out.append(f"\\item {inline(content)}")
            i += 1
            continue

        # continuation of a list item (indented non-empty, not new item)
        if in_list and ln.startswith("  ") and stripped and not stripped.startswith("|"):
            out.append(inline(stripped))
            i += 1
            continue

        # blank line
        if not stripped:
            close_list()
            out.append("")
            i += 1
            continue

        # ordinary paragraph
        close_list()
        out.append(inline(stripped))
        out.append("")
        i += 1

    close_list()
    DST.write_text("\n".join(out), encoding="utf-8")

if __name__ == "__main__":
    main()
