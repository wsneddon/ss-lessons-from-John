#!/usr/bin/env python3
"""Convert plain scripture references to BibleGateway links in lesson .qmd files."""

import re
import sys
from pathlib import Path

# Book name normalization
BOOK_MAP = {
    "genesis": "Genesis", "gen": "Genesis",
    "exodus": "Exodus", "ex": "Exodus",
    "leviticus": "Leviticus", "lev": "Leviticus",
    "numbers": "Numbers", "num": "Numbers",
    "deuteronomy": "Deuteronomy", "deut": "Deuteronomy",
    "joshua": "Joshua", "josh": "Joshua",
    "judges": "Judges",
    "ruth": "Ruth",
    "1 samuel": "1+Samuel", "1samuel": "1+Samuel",
    "2 samuel": "2+Samuel", "2samuel": "2+Samuel",
    "1 kings": "1+Kings", "1kings": "1+Kings",
    "2 kings": "2+Kings", "2kings": "2+Kings",
    "1 chronicles": "1+Chronicles", "2 chronicles": "2+Chronicles",
    "ezra": "Ezra", "nehemiah": "Nehemiah",
    "esther": "Esther", "job": "Job",
    "psalm": "Psalm", "psalms": "Psalm", "ps": "Psalm",
    "proverbs": "Proverbs", "prov": "Proverbs",
    "ecclesiastes": "Ecclesiastes",
    "song of solomon": "Song+of+Solomon",
    "isaiah": "Isaiah", "isa": "Isaiah",
    "jeremiah": "Jeremiah", "jer": "Jeremiah",
    "lamentations": "Lamentations",
    "ezekiel": "Ezekiel", "ezek": "Ezekiel",
    "daniel": "Daniel", "dan": "Daniel",
    "hosea": "Hosea", "joel": "Joel", "amos": "Amos",
    "obadiah": "Obadiah", "jonah": "Jonah", "micah": "Micah",
    "nahum": "Nahum", "habakkuk": "Habakkuk", "zephaniah": "Zephaniah",
    "haggai": "Haggai", "zechariah": "Zechariah", "malachi": "Malachi",
    "matthew": "Matthew", "matt": "Matthew",
    "mark": "Mark", "luke": "Luke", "john": "John",
    "acts": "Acts",
    "romans": "Romans", "rom": "Romans",
    "1 corinthians": "1+Corinthians", "1corinthians": "1+Corinthians",
    "2 corinthians": "2+Corinthians", "2corinthians": "2+Corinthians",
    "galatians": "Galatians", "gal": "Galatians",
    "ephesians": "Ephesians", "eph": "Ephesians",
    "philippians": "Philippians", "phil": "Philippians",
    "colossians": "Colossians", "col": "Colossians",
    "1 thessalonians": "1+Thessalonians", "2 thessalonians": "2+Thessalonians",
    "1 timothy": "1+Timothy", "2 timothy": "2+Timothy",
    "titus": "Titus", "philemon": "Philemon",
    "hebrews": "Hebrews", "heb": "Hebrews",
    "james": "James",
    "1 peter": "1+Peter", "2 peter": "2+Peter",
    "1 john": "1+John", "2 john": "2+John", "3 john": "3+John",
    "jude": "Jude",
    "revelation": "Revelation", "rev": "Revelation",
}

def make_url(book_url, ref):
    """Build a BibleGateway URL."""
    ref_encoded = ref.replace(":", "%3A").replace(" ", "+").replace("–", "-").replace("—", "-")
    return f"https://www.biblegateway.com/passage/?search={book_url}+{ref_encoded}&version=WEB"

def normalize_book(raw):
    key = raw.strip().lower()
    return BOOK_MAP.get(key)

def linkify(text):
    """Replace plain scripture refs with HTML links, skipping already-linked ones."""
    # Pattern: Book Chapter:Verse (with optional ranges and multiple verses)
    # Matches: "John 3:16", "Matthew 16:16", "1 John 2:1–3", "Genesis 3:15"
    pattern = re.compile(
        r'(?<!["\'/=>])'           # not inside an href
        r'\b((?:\d\s+)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'  # book name
        r'\s+(\d+:\d+(?:[–\-]\d+)?(?:,\s*\d+)?(?:–\d+:\d+)?)'  # chapter:verse
        r'(?![^<]*</a>)'           # not already inside an <a> tag
    )

    def replace(m):
        full = m.group(2) if m.group(2) else m.group(0)
        # Extract book and ref from the full match
        parts = re.match(r'((?:\d\s+)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(\d+:\d+.*)', full)
        if not parts:
            return full
        book_raw = parts.group(1)
        ref = parts.group(2)
        book_url = normalize_book(book_raw)
        if not book_url:
            return full
        url = make_url(book_url, ref)
        return f'<a href="{url}" target="_blank">{full}</a>'

    # Only process lines that don't already have an href containing this ref
    lines = text.split('\n')
    result = []
    for line in lines:
        # Skip lines that are already fully linked (href present)
        # Apply replacement only to text outside existing <a> tags
        new_line = re.sub(
            r'(<a\b[^>]*>.*?</a>)|'  # capture existing links (skip)
            r'(\b(?:\d\s+)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s+\d+:\d+(?:[–\-]\d+)?(?:,\s*\d+)?(?:–\d+:\d+)?)',
            lambda m: m.group(1) if m.group(1) else (replace(m) if m.group(2) else m.group(0)),
            line,
            flags=re.DOTALL
        )
        result.append(new_line)
    return '\n'.join(result)


def process_file(path: Path):
    text = path.read_text()
    new_text = linkify(text)
    if new_text != text:
        path.write_text(new_text)
        count = new_text.count('biblegateway') - text.count('biblegateway')
        print(f"{path.name}: added {count} link(s)")
    else:
        print(f"{path.name}: no changes")


if __name__ == "__main__":
    files = sys.argv[1:] or ["02 - Jesus as God/jesus-as-god.qmd"]
    base = Path(__file__).parent
    for f in files:
        process_file(base / f)
