#!/usr/bin/env python3
"""Convert revealjs lesson .qmd files to PDF-friendly handout .qmd files."""

import re
from pathlib import Path
from html.parser import HTMLParser

LESSONS = [
    "01-Intro/introduction.qmd",
    "02 - Jesus as God/jesus-as-god.qmd",
    "03 - Jesus in Creation/jesus-in-creation.qmd",
    "04 - Jesus aa life and light/jesus-life-light.qmd",
    "05 - Jesus in Salvation/jesus-in-salvation.qmd",
    "05 - Jesus grace truth and the law/grace-truth-law.qmd",
    "06 - Jesus and the Holy Spirit/holy-spirit.qmd",
    "07 - Jesus the Only way to the Father/only-way.qmd",
    "08 - Jesus priestly prayer/priestly-prayer.qmd",
]

INDENT_MAP = {
    "h2": ("# ", ""),
    "strong": ("**", "**"),  # inside summary → heading
}

# CSS class → indent prefix (using unicode thin spaces to avoid pandoc code-block trigger)
CLASS_INDENT = {
    "lv-1":         "",
    "lv-1-gap":     "",
    "lv-lc":        "\u2003",        # 1 em-space
    "lv-lc-italic": "\u2003",
    "lv-detail":    "\u2003\u2003",  # 2 em-spaces
}


class HandoutParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.lines = []
        self._stack = []       # tag stack
        self._summary_depth = 0
        self._in_summary = False
        self._summary_level = 0  # nesting depth of <details>
        self._details_depth = 0
        self._current_class = None
        self._buf = ""
        self._link_href = ""
        self._link_text = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self._stack.append(tag)
        if tag == "details":
            self._details_depth += 1
        elif tag == "summary":
            self._in_summary = True
            self._summary_level = self._details_depth
            self._buf = ""
        elif tag in ("div",):
            self._current_class = attrs.get("class", "")
            self._buf = ""
        elif tag == "h2":
            self._buf = ""
        elif tag == "a":
            self._buf += ""  # links: just keep text
            self._link_href = attrs.get("href", "")

    def handle_endtag(self, tag):
        if self._stack and self._stack[-1] == tag:
            self._stack.pop()

        if tag == "summary":
            self._in_summary = False
            text = self._buf.strip()
            level = self._summary_level
            if level == 1:
                self.lines.append(f"\n## {text}\n")
            elif level == 2:
                self.lines.append(f"\n### {text}\n")
            else:
                self.lines.append(f"\n#### {text}\n")
            self._buf = ""
        elif tag == "a":
            if self._link_href:
                link_text = self._link_text.strip() or self._link_href
                self._buf += f"[{link_text}]({self._link_href})"
                self._link_href = ""
                self._link_text = ""
        elif tag == "div":
            # Flush any unclosed <a> tag
            if self._link_href:
                link_text = self._link_text.strip() or self._link_href
                self._buf += f"[{link_text}]({self._link_href})"
                self._link_href = ""
                self._link_text = ""
            text = self._buf.strip()
            if text:
                indent = CLASS_INDENT.get(self._current_class, "")
                # Strip leading em-dash used as bullet in source
                text = re.sub(r'^—\s*', '• ', text)
                self.lines.append(f"{indent}{text}\n\n")
            self._buf = ""
            self._current_class = None
        elif tag == "h2":
            text = self._buf.strip()
            if text:
                self.lines.append(f"# {text}\n\n")
            self._buf = ""
        elif tag == "details":
            self._details_depth -= 1

    def handle_data(self, data):
        if self._stack and self._stack[-1] == "a":
            self._link_text += data  # track separately, don't add to buf yet
        elif self._in_summary or self._current_class or (self._stack and self._stack[-1] == "h2"):
            self._buf += data

    def get_markdown(self):
        return "".join(self.lines)


def extract_title(qmd_text):
    m = re.search(r"<h2[^>]*>(.*?)</h2>", qmd_text, re.DOTALL)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    return "Lesson"


def convert(src_path: Path) -> str:
    text = src_path.read_text()
    # Extract the HTML block
    m = re.search(r"```\{=html\}(.*?)```", text, re.DOTALL)
    if not m:
        return ""
    html = m.group(1)
    title = extract_title(html)

    parser = HandoutParser()
    parser.feed(html)
    md = parser.get_markdown()

    header = f"""---
title: "{title}"
format:
  pdf:
    toc: false
    number-sections: false
    geometry: margin=1in
    fontsize: 11pt
    pdf-engine: xelatex
mainfont: "Arial"
---

"""
    return header + md


def main():
    base = Path(__file__).parent
    handout_paths = []

    for lesson in LESSONS:
        src = base / lesson
        if not src.exists():
            print(f"SKIP (not found): {lesson}")
            continue
        stem = src.stem
        out = src.parent / f"{stem}-handout.qmd"
        content = convert(src)
        if not content:
            print(f"SKIP (no html block): {lesson}")
            continue
        out.write_text(content)
        print(f"Created: {out.relative_to(base)}")
        handout_paths.append(str(out.relative_to(base)))

    # Update _quarto.yml render list
    yml_path = base / "_quarto.yml"
    yml = yml_path.read_text()

    # Remove old handout entries if any
    yml = re.sub(r'\s*- "?[^"\n]*-handout\.qmd"?\n', "", yml)

    # Remove pdf: default if present (handouts have their own format)
    yml = re.sub(r'\s*pdf: default\n', "\n", yml)

    # Append handout paths to render list
    additions = ""
    for p in handout_paths:
        q = f'"{p}"' if " " in p else p
        additions += f"  - {q}\n"

    yml = yml.rstrip() + "\n" + additions
    yml_path.write_text(yml)
    print(f"\nUpdated _quarto.yml with {len(handout_paths)} handout(s).")


if __name__ == "__main__":
    main()
