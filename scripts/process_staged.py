#!/usr/bin/env python3
"""
Process staged JSON from scrape.py into hub.db.

Handles mechanical tagging (source affiliation, grade level, keyword matching)
and inserts entries into the SQLite database. Backlog items (found on the
listing but without a usable description) are inserted as excluded rows with
exclude_reason='no_description_pending' so scrape.py's diff and early-stop
treat them as known and they stop showing up as "new" every run; a later
backfill fills the description and clears `excluded`. Each active row records
description_source (listing / page-meta / page-abstract) from the staged
item's blurb_source, written by scrape.py.

Usage:
    python scripts/process_staged.py wwc                # process all ready items
    python scripts/process_staged.py wwc --limit 5      # process first 5 items
    python scripts/process_staged.py wwc --preview       # show entries without writing
    python scripts/process_staged.py wwc --offset 10     # skip first 10 items

After processing, run `python scripts/build_from_db.py` to regenerate published files.
"""
import argparse
import json
import re
import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from scrape import url_key  # same dedup key as hub.db's unique index

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
STAGING_DIR = REPO_ROOT / "docs" / "staging"
DB_PATH = REPO_ROOT / "data" / "hub.db"
PROCESSING_LOG = REPO_ROOT / "meta" / "processing-log.md"

TODAY = date.today().isoformat()
PENDING_REASON = "no_description_pending"

SOURCE_TAG_MAP = {
    "wwc": "wwc",
    "wwc-practice-guides": "wwc",
    "lpi": "lpi",
    "lpi-briefs": "lpi",
    "lpi-fact-sheets": "lpi",
    "digital-promise": "digital-promise",
    "edtrust": "edtrust",
    "wested": None,
    "nwea-research": None,
    "brookings": "brookings",
    "tntp": None,
    "uchicago-consortium": None,
    "campbell-collaboration": "campbell-collaboration",
    "evidence-for-essa": None,
    "mathematica": None,
    "jedm": "jedm",
    "jla": "jla",
    "casel": None,
}

SOURCE_NAME_MAP = {
    "wwc": "What Works Clearinghouse",
    "wwc-practice-guides": "What Works Clearinghouse",
    "lpi": "Learning Policy Institute",
    "lpi-briefs": "Learning Policy Institute",
    "lpi-fact-sheets": "Learning Policy Institute",
    "digital-promise": "Digital Promise",
    "edtrust": "The Education Trust",
    "wested": "WestEd",
    "nwea-research": "NWEA Research",
    "brookings": "Brookings Institution",
    "tntp": "TNTP",
    "aims-collaboratory": "AIMS Collaboratory",
    "uchicago-consortium": "UChicago Consortium on School Research",
    "campbell-collaboration": "Campbell Collaboration",
    "evidence-for-essa": "Evidence for ESSA",
    "mathematica": "Mathematica",
    "credo": "CREDO at Stanford",
    "jedm": "Journal of Educational Data Mining",
    "jla": "Journal of Learning Analytics",
    "casel": "CASEL",
}

TYPE_MAP = {
    "intervention report": "report",
    "practice guide": "framework",
    "report": "report",
    "brief": "report",
    "article": "paper",
    "book": "report",
    "snapshot": "report",
    "blog": "blog-post",
    "video": "presentation",
    "research": "report",
    "commentary": "blog-post",
    "training and professional development": "framework",
    "webinar": "presentation",
    "issue brief": "report",
    "resource guide": "framework",
    "toolkit": "tool",
    "reading": "report",
    "math": "report",
    "social-emotional": "report",
    "attendance": "report",
    "science": "report",
    "family engagement": "report",
    "project report": "report",
    "journal article": "paper",
    "working paper": "paper",
    "professional or conference paper": "paper",
    "executive summary": "report",
    "survey instrument": "tool",
    "book chapter": "paper",
    "paper": "paper",
    "guide": "framework",
    "family playbook": "framework",
    "model paper": "paper",
    "literature review": "review",
    # WestEd library labels (2026-08-30 backfill)
    "research and evaluation": "report",
    "case study": "report",
    "collection": "report",
    "edited volume": "report",
    "data visualization and infographic": "report",
    "tool": "tool",
    "assessment resource": "tool",
    "curriculum": "framework",
    "wested perspectives": "report",  # a brief series, despite the blog-like name (2026-08-30)
    "audiocast": "presentation",
    # EdTrust type-of-content labels (2026-08-30 backfill)
    "compilation": "report",
    "fact sheet": "report",
    "podcast": "presentation",
    "data tool": "tool",
    "digital report": "report",
    "infographic": "report",
    "presentation": "presentation",
    "data set": "dataset",
    "testimony": "report",
    "appendix": "report",
    "other": "report",
}

GRADE_TAG_MAP = {
    "pk": "prekindergarten",
    "pre-k": "prekindergarten",
    "prek": "prekindergarten",
    "k": "k-12",
    "ps": "higher-ed",
    "postsecondary": "higher-ed",
}

KEYWORD_TAGS = [
    (r'\breading\b|phonics|phonemic|phonological|read(ers?|ability)\b|literacy|decod(e|ing)\b|vocabulary|comprehension|oral reading|beginning reading|reading fluency|reading instruction', "literacy"),
    (r'\bmath|algebra|arithmetic|calcul|numer(acy|ical)|geometry|fraction|equation', "math-education"),
    (r'\benglish learner|bilingual|esl\b|english language learner|dual.language|multilingual', "english-learners"),
    (r'\bsocial.emotional|sel\b|behavio(r|ur|ral)|social skills|emotional|self.regulation|character', "sel"),
    (r'\bdropout|graduation rate|credit recovery|staying in school|leaving school', "dropout-prevention"),
    (r'\battendance|absent|chronic absence|truancy', "attendance"),
    (r'\bcollege|postsecondary|university|undergraduate|higher education', "college-access"),
    (r'\bprekindergarten|preschool|pre.k\b|head start|early childhood|ages? [3-5]|toddler', "early-childhood"),
    (r'\bwriting|composition|essay|written expression', "writing-instruction"),
    (r'\bprofessional development|teacher training|teacher preparation|coaching|mentoring', "professional-development"),
    (r'\bassessment|formative|diagnostic test|screening|progress monitor', "formative-assessment"),
    (r'\btutor|intervention|remediat|supplemental instruction|response to intervention|rti\b', "response-to-intervention"),
    (r'\btechnology|computer|digital|software|online|web.based|app\b|tablet|device', "computer-assisted-learning"),
    (r'\bpersonaliz|adaptive|individuali[zs]ed instruction|differentiat', "personalized-learning"),
    (r'\bstem\b|science education|science instruction|science achievement', "k-12"),
    (r'\bspecial education|disabilit|iep\b|inclusion|inclusive', "inclusive-design"),
    (r'\bcareer|workforce|vocational|cte\b|career.technical', "career-readiness"),
    (r'\bdata.driven|data.use|data.based|learning analytics', "learning-engineering"),
]


EXTRA_COLUMNS = {
    # Everything the scraper collected for the row, as staged (JSON): listing
    # fields, API extras, page_meta from a detail fetch. Kept so later passes
    # (tagging, type review, description upgrades) never need a re-fetch.
    "raw_item": "TEXT",
    # The publisher's own topic labels for the item (JSON list), unmapped.
    "source_subjects": "TEXT",
    # Structured metadata + a per-field provenance column each, mirroring
    # description_source. Provenance records whether a value came from the
    # source of truth (listing / page-meta) or was LLM-extracted. See
    # METADATA_FIELDS; add a field by adding its two columns here plus one
    # registry entry.
    "published_date": "TEXT",       # ISO, granularity as given (YYYY / YYYY-MM / YYYY-MM-DD)
    "date_source": "TEXT",
    "authors": "TEXT",              # JSON list of names
    "authors_source": "TEXT",
    "grade_level": "TEXT",          # plain string when the source states one
    "grade_level_source": "TEXT",
    "document_url": "TEXT",         # direct link to the report file (PDF) when the source offers one
    "document_url_source": "TEXT",
}


def ensure_columns(conn):
    """Add any missing EXTRA_COLUMNS to entries (idempotent)."""
    have = {r[1] for r in conn.execute("PRAGMA table_info(entries)")}
    for col, typ in EXTRA_COLUMNS.items():
        if col not in have:
            conn.execute(f"ALTER TABLE entries ADD COLUMN {col} {typ}")


def get_db():
    # Writer: BEGIN IMMEDIATE takes the write lock up front so the 30 s busy
    # timeout applies (a deferred read->write upgrade fails at once instead).
    conn = sqlite3.connect(DB_PATH, timeout=30, isolation_level="IMMEDIATE")
    conn.execute("PRAGMA foreign_keys=ON")
    ensure_columns(conn)
    return conn


def _raw_json(item):
    return json.dumps(item, ensure_ascii=False, sort_keys=True)


def _subjects_json(item):
    tags = item.get("tags")
    if isinstance(tags, list) and tags:
        return json.dumps([str(t) for t in tags], ensure_ascii=False)
    if isinstance(tags, str) and tags.strip():
        return json.dumps([tags.strip()], ensure_ascii=False)
    return None


_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}


EPOCH_TZ = ZoneInfo("America/New_York")  # calendar day for epoch-ms dates


def _norm_date(val):
    """Normalise a publisher date to ISO, keeping only the granularity given:
    'YYYY', 'YYYY-MM', or 'YYYY-MM-DD'. Returns None when unparseable — a date
    we can't trust for sorting is better absent than guessed."""
    if not val:
        return None
    s = str(val).strip()
    if re.match(r"^\d{12,13}$", s):
        # Epoch milliseconds (Mathematica's Coveo index). The publisher enters
        # the date in US Eastern time and the index stores it as UTC, so an
        # evening entry reads as the next UTC day; take the Eastern calendar
        # day, which is what the item page displays (checked 2026-09-15).
        return datetime.fromtimestamp(int(s) / 1000, EPOCH_TZ).strftime("%Y-%m-%d")
    m = re.match(r"^(\d{4})[-/](\d{2})(?:[-/](\d{2}))?", s)   # ISO, or OJS's 2025/04/23
    if m:
        return _iso(m.group(1), m.group(2), m.group(3))
    m = re.match(r"^([A-Za-z]+)\.?\s+(?:(\d{1,2}),?\s+)?(\d{4})$", s)
    if m and m.group(1).lower() in _MONTHS:
        return _iso(m.group(3), _MONTHS[m.group(1).lower()], m.group(2))
    m = re.match(r"^(\d{4})$", s)
    if m:
        return m.group(1)
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", s)
    if m:
        # US-style MM/DD/YYYY (CREDO's listing, 2026-09-16); every source that
        # emits this shape is US-based. A day > 12 in the first slot is not a date.
        return _iso(m.group(3), m.group(1), m.group(2))
    return None


def _iso(year, month, day=None):
    """Assemble YYYY-MM[-DD], or None when the month or day is out of range."""
    month, day = int(month), (int(day) if day else None)
    if not 1 <= month <= 12 or (day is not None and not 1 <= day <= 31):
        return None
    return f"{year}-{month:02d}-{day:02d}" if day else f"{year}-{month:02d}"


_BYLINE_PREFIX = re.compile(r"^\s*(?:by|authors?)\s*:?\s+", re.I)
MAX_AUTHOR_CHARS = 80   # longer than any name: a paragraph the selector caught


def _split_byline(text):
    """'By: A, B, and C' -> ['A', 'B', 'C']. A string without a By/Authors
    prefix is one name; anything longer than a name is rejected (NWEA's
    .author selector once matched an abstract paragraph, 2026-09-16)."""
    text = text.strip()
    if _BYLINE_PREFIX.match(text):
        text = _BYLINE_PREFIX.sub("", text)
        parts = re.split(r"\s*,\s*|\s+and\s+|\s*;\s*|\s*&\s*", text)
    elif "," in text and all(_looks_like_name(p) for p in re.split(r"\s*,\s*|\s+and\s+", text) if p.strip()):
        # "Katharine Meyer, Isabel McMullen" (Brookings byline, no prefix):
        # every comma-separated piece is shaped like a full name, so it is a
        # list. "Doe, Jane" has a one-word piece and stays one name; a
        # sentence with commas fails the shape test and stays one (rejected
        # below for length).
        parts = re.split(r"\s*,\s*|\s+and\s+", text)
    else:
        parts = [text]
    names = [p.strip().rstrip(".").strip() for p in parts]
    return [n for n in names if n and len(n) <= MAX_AUTHOR_CHARS and not _CREDENTIAL.match(n)]


_NAME_PARTICLES = {"de", "da", "del", "della", "di", "du", "la", "le", "van", "von", "der", "den", "y", "e", "bin", "al"}


def _looks_like_name(piece):
    """2-4 words, each capitalised (or a particle like 'van'), no sentence
    punctuation: 'Isabel McMullen', 'Scott J. Peters', 'Maria del Rosario'."""
    words = piece.strip().split()
    if not 2 <= len(words) <= 4:
        return False
    return all(w[:1].isupper() or w.lower() in _NAME_PARTICLES for w in words) and not re.search(r"[()=:;]", piece)


# A comma-split token that is a credential, not a person ("Naomi Duran, PhD")
_CREDENTIAL = re.compile(r"^(?:ph\.?\s?d|ed\.?\s?d|m\.?\s?[aes]d?|m\.?p\.?[ah]|m\.?s\.?w|psy\.?d|j\.?d|dr|jr|sr|iii?|iv)\.?$", re.I)


def _authors_json(val):
    """Normalise an author value (list or string) to a JSON list of names."""
    if not val:
        return None
    if isinstance(val, str):
        val = [val]
    names = [n for a in val for n in _split_byline(str(a))]
    return json.dumps(names, ensure_ascii=False) if names else None


def apply_metadata_map(items, config):
    """A config's "metadata_map" {field: raw key} copies a value the scrape
    stored under another key (NWEA's detail fetch kept the page byline as
    authors_page and the page date as date_page while the API's own fields
    were empty or wrong, 2026-09-16) onto the field the registry reads.
    The mapped key is authoritative: it replaces whatever the field held (the
    NWEA API's post date is exactly the value to override). A key that the
    config's detail_fetch extra_fields supplied is recorded in detail_fields
    so it labels page-meta."""
    mapping = (config or {}).get("metadata_map") or {}
    page_keys = set(((config or {}).get("detail_fetch") or {}).get("extra_fields") or {})
    for item in items:
        for field, key in mapping.items():
            if not item.get(key):
                continue
            item[field] = item[key]
            if key in page_keys:
                item.setdefault("detail_fields", [])
                if field not in item["detail_fields"]:
                    item["detail_fields"].append(field)
    return items


PAGE_META_DATE_KEYS = ("citation_publication_date", "citation_date", "bepress_citation_date",
                       "dc.date.issued", "dc.date", "citation_online_date", "bepress_citation_online_date",
                       "article:published_time", "jsonld:datePublished")
PAGE_META_AUTHOR_KEYS = ("citation_author", "bepress_citation_author", "dc.creator")
PAGE_META_PDF_KEYS = ("citation_pdf_url", "bepress_citation_pdf_url")


def apply_page_meta_fallback(items):
    """Fill date / authors / document_url from the page's standard metadata
    tags (scrape.py's page_meta: citation_*, bepress_*, DC.*, article:*,
    schema.org datePublished) when no selector supplied them (2026-09-16:
    AIMS entries spread over 20 repository and journal hosts). Page-supplied,
    so the field is recorded in detail_fields and labels page-meta."""
    for item in items:
        meta = item.get("page_meta") or {}
        if not meta:
            continue
        for field, keys in (("date", PAGE_META_DATE_KEYS), ("authors", PAGE_META_AUTHOR_KEYS),
                            ("document_url", PAGE_META_PDF_KEYS)):
            if item.get(field):
                continue
            val = next((meta[k] for k in keys if meta.get(k)), None)
            if not val:
                continue
            item[field] = val
            item.setdefault("detail_fields", [])
            if field not in item["detail_fields"]:
                item["detail_fields"].append(field)
    return items


def load_source_config(slug):
    """The source's sources/<slug>.json, or {} when there is none (hand-curated
    sources have no config)."""
    path = REPO_ROOT / "sources" / f"{slug}.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _grade_level(val):
    """Grade / education level as a plain string, when the source states one."""
    if not val:
        return None
    return str(val).strip() or None


# Structured metadata backfilled from a staged item. Each field is paired with
# the column that records its provenance, the raw item keys the value is read
# from, and the extractor. Add a field by adding one entry here plus its two
# EXTRA_COLUMNS.
METADATA_FIELDS = {
    "published_date": ("date_source", ("date",), lambda it: _norm_date(it.get("date"))),
    "authors": ("authors_source", ("authors",), lambda it: _authors_json(it.get("authors"))),
    "grade_level": ("grade_level_source", ("grade", "grade_level"),
                    lambda it: _grade_level(it.get("grade") or it.get("grade_level"))),
    "document_url": ("document_url_source", ("document_url", "pdf_url"),
                     lambda it: _document_url(it.get("document_url") or it.get("pdf_url"))),
}


def _document_url(val):
    """An absolute http(s) link to the report file, or None (2026-09-16)."""
    if not val:
        return None
    if isinstance(val, list):
        val = val[0] if val else None
    s = str(val or "").strip()
    return s if s.lower().startswith(("http://", "https://")) else None

METADATA_SOURCES = ("listing", "page-meta", "prose", "url", "llm", "manual")


def apply_url_date_inference(items, config):
    """A config's "date_from_url" rules infer a date from the URL itself when
    nothing else supplied one (2026-09-16, user: inference is fine if flagged):
    [{"host": "e4.northwestern.edu", "regex": "/(\\d{4})/(\\d{2})/(\\d{2})/"},
     {"regex": "-(20\\d{2})(?:-\\d)?/?$"}]. The regex groups are year[, month[,
    day]]; the value is stamped date_source "url" via item["field_sources"]."""
    rules = (config or {}).get("date_from_url") or []
    for item in items:
        if item.get("date") or not item.get("url"):
            continue
        for rule in rules:
            if rule.get("host") and _host_of(item["url"]) != rule["host"].lower():
                continue
            m = re.search(rule["regex"], item["url"])
            if not m:
                continue
            item["date"] = "-".join(g for g in m.groups() if g)
            item.setdefault("field_sources", {})["date"] = "url"
            break
    return items


def _host_of(url):
    m = re.match(r"^https?://(?:www\.)?([^/]+)", url or "")
    return m.group(1).lower() if m else ""


def _meta_source_label(item, raw_keys=()):
    """Where a structured field's value came from: 'page-meta' when the item
    page supplied it (scrape.py's detail_fetch extra_fields records the keys it
    filled in item['detail_fields']), otherwise 'listing' — the listing page or
    API. Independent of blurb_source, which describes the description only.
    The LLM fallback path stamps 'llm' explicitly on the fields it fills."""
    explicit = (item.get("field_sources") or {})
    for k in raw_keys:
        if explicit.get(k) in METADATA_SOURCES:
            return explicit[k]          # an inference stamped its own label ("url", "prose")
    detail_fields = item.get("detail_fields") or ()
    return "page-meta" if any(k in detail_fields for k in raw_keys) else "listing"


def backfill_metadata(conn, items, overwrite=False):
    """Fill METADATA_FIELDS (+ source_subjects) on EXISTING rows matched by URL.
    Never inserts, never touches description / tags / excluded, and does not
    bump updated_at. By default only empty fields are filled; overwrite=True
    replaces them. The staged item itself is kept as raw_item under the same
    rule, so a field mapped later can be derived locally instead of by another
    fetch (2026-09-15). Returns (counts_by_field, matched, unmatched)."""
    ensure_columns(conn)
    rows = {url_key(u): num for num, u in conn.execute("SELECT num, url FROM entries")}
    fields = list(METADATA_FIELDS)
    counts = {f: 0 for f in fields}
    counts["source_subjects"] = 0
    counts["raw_item"] = 0
    matched = unmatched = 0
    for item in items:
        url = (item.get("url") or "").strip()
        num = rows.get(url_key(url)) if url else None
        if num is None:
            unmatched += 1
            continue
        matched += 1
        row = conn.execute(
            f"SELECT {', '.join(fields)}, source_subjects, raw_item FROM entries WHERE num=?", (num,)
        ).fetchone()
        current = dict(zip(fields + ["source_subjects", "raw_item"], row))
        sets, vals = [], []
        for field, (src_col, raw_keys, extract) in METADATA_FIELDS.items():
            value = extract(item)
            if value is None or (current[field] and not overwrite):
                continue
            sets += [f"{field}=?", f"{src_col}=?"]
            vals += [value, _meta_source_label(item, raw_keys)]
            counts[field] += 1
        subjects = _subjects_json(item)
        if subjects and (overwrite or not current["source_subjects"]):
            sets.append("source_subjects=?")
            vals.append(subjects)
            counts["source_subjects"] += 1
        if (overwrite or not current["raw_item"]) and not item.get("_stub"):
            sets.append("raw_item=?")
            vals.append(_raw_json(item))
            counts["raw_item"] += 1
        if sets:
            vals.append(num)
            conn.execute(f"UPDATE entries SET {', '.join(sets)} WHERE num=?", vals)
    return counts, matched, unmatched


def items_from_db(conn, source_name):
    """The stored raw listing records of a source's rows, as staged-style items,
    so a field mapped after the scrape can be backfilled without a request
    (2026-09-15: EdTrust/UChicago/NWEA dates already sat in raw_item)."""
    items = []
    for url, raw in conn.execute(
            "SELECT url, raw_item FROM entries WHERE source=? AND excluded=0", (source_name,)):
        if not raw:
            # No stored record: a URL-only stub, so URL-based inference can
            # still run; never written back as raw_item.
            items.append({"url": url, "_stub": True})
            continue
        try:
            item = json.loads(raw)
        except (TypeError, ValueError):
            continue
        if isinstance(item, dict):
            item.setdefault("url", url)
            items.append(item)
    return items


def _verified_fields(item):
    """A detail fetch that returned 200 already proves the URL is live: record it
    so verify_urls.py does not request the same page again."""
    if item.get("fetched_status") == 200:
        return ("verified", "200", item.get("fetched_at") or TODAY)
    return ("unverified", None, None)


def get_last_entry_num():
    conn = get_db()
    row = conn.execute("SELECT MAX(num) FROM entries").fetchone()
    conn.close()
    return row[0] or 0


def infer_type(item):
    raw = item.get("type", "").strip().lower()
    return TYPE_MAP.get(raw, "report")


def insert_backlog_rows(conn, backlog_items, source_name, start_num):
    """Insert backlog items as excluded, pending rows. Skips URLs already in
    hub.db (active or excluded) and repeats within the batch. Returns
    (inserted_count, last_num_used)."""
    existing = {url_key(r[0]) for r in conn.execute("SELECT url FROM entries")}
    num = start_num
    inserted = 0
    for item in backlog_items:
        url = (item.get("url") or "").strip()
        if not url or url_key(url) in existing:
            continue
        existing.add(url_key(url))
        title = (item.get("title") or "").strip() or url
        url_status, http_status, verified_on = _verified_fields(item)
        conn.execute("""
            INSERT INTO entries (num, title, url, type, source, url_confirmed,
                description_inferred, date_added, doi, license, description,
                url_status, url_http_status, last_verified, excluded, exclude_reason,
                raw_item, source_subjects)
            VALUES (?, ?, ?, ?, ?, 0, 0, ?, NULL, NULL, '', ?, ?, ?, 1, ?, ?, ?)
        """, (num, title, url, infer_type(item), source_name, TODAY, url_status, http_status,
              verified_on, PENDING_REASON, _raw_json(item), _subjects_json(item)))
        num += 1
        inserted += 1
    return inserted, num - 1


def insert_filtered_rows(conn, filtered_items, source_name, start_num):
    """Insert items the type filter set aside as excluded rows with reason
    'type_filtered:<label>', keeping title, URL, any blurb and the raw item, so
    the scope call can be reversed with curate.py reactivate. Returns
    (inserted_count, last_num_used)."""
    existing = {url_key(r[0]) for r in conn.execute("SELECT url FROM entries")}
    num = start_num
    inserted = 0
    for item in filtered_items:
        url = (item.get("url") or "").strip()
        if not url or url_key(url) in existing:
            continue
        existing.add(url_key(url))
        title = (item.get("title") or "").strip() or url
        blurb = (item.get("blurb") or "").strip()
        desc_source = item.get("blurb_source") if blurb else None
        if desc_source not in DESCRIPTION_SOURCES:
            desc_source = None
        reason = item.get("filter_reason") or "type_filtered:unknown"
        url_status, http_status, verified_on = _verified_fields(item)
        conn.execute("""
            INSERT INTO entries (num, title, url, type, source, url_confirmed,
                description_inferred, date_added, doi, license, description,
                url_status, url_http_status, last_verified, excluded, exclude_reason,
                description_source, raw_item, source_subjects)
            VALUES (?, ?, ?, ?, ?, 1, 0, ?, NULL, NULL, ?, ?, ?, ?, 1, ?, ?, ?, ?)
        """, (num, title, url, infer_type(item), source_name, TODAY, blurb, url_status, http_status,
              verified_on, reason, desc_source, _raw_json(item), _subjects_json(item)))
        num += 1
        inserted += 1
    return inserted, num - 1


DESCRIPTION_SOURCES = ("listing", "page-meta", "page-abstract", "llm-summary", "manual")


def insert_items(conn, items, source_slug, source_name, start_num):
    """Insert ready items as active rows numbered from start_num; returns the
    count inserted. description_source comes from the item's blurb_source
    (scrape.py writes 'listing' or the detail_fetch label); a staging file
    without it, or with an unknown value, gets NULL rather than a guess."""
    inserted = 0
    for i, item in enumerate(items):
        num = start_num + i
        blurb = item.get("blurb", "").strip()
        desc_source = item.get("blurb_source")
        if desc_source not in DESCRIPTION_SOURCES:
            desc_source = None
        url_status, http_status, verified_on = _verified_fields(item)
        conn.execute("""
            INSERT INTO entries (num, title, url, type, source, url_confirmed,
                description_inferred, date_added, doi, license, description,
                url_status, url_http_status, last_verified, description_source,
                raw_item, source_subjects)
            VALUES (?, ?, ?, ?, ?, 1, 0, ?, NULL, NULL, ?, ?, ?, ?, ?, ?, ?)
        """, (num, item["title"].strip(), item["url"].strip(), infer_type(item),
              source_name, TODAY, blurb, url_status, http_status, verified_on, desc_source,
              _raw_json(item), _subjects_json(item)))
        for tag in infer_tags(item, source_slug):
            conn.execute("INSERT OR IGNORE INTO entry_tags (entry_num, tag) VALUES (?, ?)", (num, tag))
        inserted += 1
    return inserted


def infer_tags(item, source):
    tags = []
    src_tag = SOURCE_TAG_MAP.get(source)
    if src_tag:
        tags.append(src_tag)

    grade = item.get("grade_level", "").lower().strip()
    if grade:
        for prefix, tag in GRADE_TAG_MAP.items():
            if prefix in grade:
                if tag not in tags:
                    tags.append(tag)
                break
        if any(c.isdigit() for c in grade) and "higher-ed" not in tags:
            if "k-12" not in tags:
                tags.append("k-12")

    tier = item.get("evidence_tier", "").strip()
    if tier == "1":
        tags.append("rct")

    text = (item.get("title", "") + " " + item.get("blurb", "")).lower()
    for pattern, tag in KEYWORD_TAGS:
        if tag not in tags and re.search(pattern, text):
            tags.append(tag)

    return tags


def main():
    parser = argparse.ArgumentParser(description="Process staged JSON into hub.db")
    parser.add_argument("source", help="Source slug matching the staged JSON filename")
    parser.add_argument("--limit", type=int, default=None, help="Process only the first N items")
    parser.add_argument("--offset", type=int, default=0, help="Skip the first N items")
    parser.add_argument("--preview", action="store_true", help="Show entries without writing to DB")
    parser.add_argument("--backfill-metadata", action="store_true",
                        help="Update EXISTING rows' date/authors/grade/subjects from the staged file (no inserts)")
    parser.add_argument("--overwrite", action="store_true",
                        help="With --backfill-metadata, replace existing values instead of filling only empties")
    parser.add_argument("--from-db", action="store_true",
                        help="With --backfill-metadata, take the items from the rows' stored raw_item "
                             "instead of the staged file (no staging file, no requests)")
    args = parser.parse_args()

    if args.from_db:
        if not args.backfill_metadata:
            parser.error("--from-db only makes sense with --backfill-metadata")
        conn = get_db()
        source_name = SOURCE_NAME_MAP.get(args.source, args.source)
        source_config = load_source_config(args.source)
        items = apply_url_date_inference(apply_page_meta_fallback(
            apply_metadata_map(items_from_db(conn, source_name), source_config)), source_config)
        print(f"[process] Source: {args.source} ({source_name}), {len(items)} stored raw items")
        counts, matched, unmatched = backfill_metadata(conn, items, overwrite=args.overwrite)
        conn.commit()
        conn.close()
        print(f"[process] Backfill metadata from db ({'overwrite' if args.overwrite else 'fill-empty'}): "
              f"matched {matched} rows; {unmatched} raw items had no row")
        for field, n in counts.items():
            print(f"    {field}: {n} rows filled")
        print("[process] Next: run `python scripts/build_from_db.py`")
        return

    staged_path = STAGING_DIR / f"{args.source}.json"
    if not staged_path.exists():
        print(f"Error: no staged file at {staged_path}", file=sys.stderr)
        sys.exit(1)

    with open(staged_path, encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("items", [])
    backlog = data.get("backlog_items", [])
    filtered = data.get("filtered_items", [])
    if not items and not backlog and not filtered:
        print("No ready, backlog or filtered items in staged file.")
        return

    items = items[args.offset:]
    if args.limit:
        items = items[:args.limit]
    source_config = load_source_config(args.source)
    for lst in (items, backlog, filtered):
        apply_url_date_inference(apply_page_meta_fallback(apply_metadata_map(lst, source_config)), source_config)

    print(f"[process] Source: {args.source}, {len(items)} items to process")

    if args.backfill_metadata:
        # Backlog and filtered items match existing (excluded) rows too; their
        # metadata is just as real, so a backfill covers all three lists.
        items = items + backlog + filtered
        conn = get_db()
        counts, matched, unmatched = backfill_metadata(conn, items, overwrite=args.overwrite)
        conn.commit()
        conn.close()
        print(f"[process] Backfill metadata ({'overwrite' if args.overwrite else 'fill-empty'}): "
              f"matched {matched} existing rows; {unmatched} staged items had no row")
        for field, n in counts.items():
            print(f"    {field}: {n} rows filled")
        print("[process] Next: run `python scripts/build_from_db.py`")
        return

    start_num = get_last_entry_num() + 1
    source_name = SOURCE_NAME_MAP.get(args.source, args.source)

    if args.preview:
        for i, item in enumerate(items[:5]):
            num = start_num + i
            tags = infer_tags(item, args.source)
            print(f"  #{num} {item['title'][:60]}")
            print(f"    type={infer_type(item)} tags={tags}")
            print(f"    url={item['url'][:70]}")
            print()
        end_num = start_num + len(items) - 1
        print(f"[process] Preview: {len(items)} entries ({start_num}-{end_num})")
        return

    conn = get_db()

    # Dedup guard: never insert a URL already in hub.db (active or excluded —
    # excluded rows are kept precisely so they aren't re-indexed), and skip
    # within-batch repeats. scrape.py's diff normally handles this, but this
    # guard makes re-running a staging file (or a --no-diff scrape) safe.
    existing_urls = {url_key(r[0]) for r in conn.execute("SELECT url FROM entries")}
    seen_batch = set()
    deduped = []
    for item in items:
        url = item["url"].strip()
        if url_key(url) in existing_urls or url_key(url) in seen_batch:
            continue
        seen_batch.add(url_key(url))
        deduped.append(item)
    if len(deduped) < len(items):
        print(f"[process] Skipped {len(items) - len(deduped)} duplicate URLs already in hub.db or repeated in batch")
    items = deduped

    inserted = insert_items(conn, items, args.source, source_name, start_num)
    end_num = start_num + inserted - 1
    if inserted:
        print(f"[process] Inserted {inserted} entries ({start_num}-{end_num}) into hub.db")
    else:
        print("[process] Nothing new to insert.")

    pending, pending_end = insert_backlog_rows(conn, backlog, source_name, start_num + inserted)
    if pending:
        print(f"[process] Backlog: {pending} pending rows ({start_num + inserted}-{pending_end}) "
              f"inserted as excluded ({PENDING_REASON})")
    filtered_n, filtered_end = insert_filtered_rows(conn, filtered, source_name, start_num + inserted + pending)
    if filtered_n:
        print(f"[process] Type filter: {filtered_n} rows ({start_num + inserted + pending}-{filtered_end}) "
              f"inserted as excluded (type_filtered:<label>)")
    conn.commit()
    conn.close()

    if inserted or pending or filtered_n:
        print("[process] Next: run `python scripts/build_from_db.py`")
        write_log(args.source, data, items, start_num, end_num, pending + filtered_n)


def write_log(source, staged_data, items, start_num, end_num, pending=0):
    source_name = SOURCE_NAME_MAP.get(source, source)
    total_staged = staged_data.get("total_ready", 0) + staged_data.get("total_backlog", 0)
    ready = staged_data.get("total_ready", 0)
    backlog = staged_data.get("total_backlog", 0)

    processed = f"- Processed: {len(items)} entries"
    if items:
        processed += f" ({start_num}-{end_num})"
    entry = (
        f"\n## {TODAY} - {source_name}\n"
        f"- Source slug: `{source}`\n"
        f"- Scraped: {total_staged} total, {ready} ready, {backlog} backlog\n"
        f"{processed}\n"
        f"- Backlog rows recorded as pending (excluded): {pending}\n"
        f"- Tags: keyword auto-tagged\n"
    )

    with open(PROCESSING_LOG, "a", encoding="utf-8") as f:
        f.write(entry)
    print(f"[process] Logged to {PROCESSING_LOG}")


if __name__ == "__main__":
    main()
