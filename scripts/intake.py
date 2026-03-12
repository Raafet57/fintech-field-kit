#!/usr/bin/env python3
"""
Intake new PDFs from a local inbox into the repo.

Workflow:
- Scan inbox for PDFs and ZIPs (ZIPs are extracted to a temp dir).
- De-duplicate against existing repo PDFs and within the batch.
- Classify into top-level categories and best-effort subfolders.
- Normalize filenames conservatively and move into the repo.
- Run scripts/build_catalog.py after adding new files.

Designed to be safe, conservative, and editable.
"""
from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

try:
    import PyPDF2  # type: ignore
except Exception as exc:  # pragma: no cover
    print(f"ERROR: PyPDF2 not available: {exc}")
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
PAPERS_ROOT = ROOT.parent  # /Users/Raafet/Projects/Papers

DEFAULT_INBOX = PAPERS_ROOT / "_inbox"
DEFAULT_DUPLICATES = PAPERS_ROOT / "_duplicates"
DEFAULT_REVIEW = PAPERS_ROOT / "_review"
DEFAULT_LOG_DIR = PAPERS_ROOT / "_logs"
DEFAULT_STATE = PAPERS_ROOT / "_intake_state.json"

# Category keywords used for lightweight classification.
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "Stablecoins_and_CBDC": [
        "stablecoin", "stablecoins", "cbdc", "central bank digital currency",
        "genius act", "usdc", "usdt", "tokenized deposit", "tokenised deposit",
    ],
    "Tokenization_Blockchain_and_Digital_Assets": [
        "tokenization", "tokenised", "tokenized", "blockchain", "digital asset",
        "cryptoasset", "crypto asset", "dlt", "web3", "smart contract",
        "tokenized securities", "tokenised securities", "security token",
    ],
    "Payments_RealTime_and_Liquidity": [
        "payment", "payments", "real-time", "realtime", "instant", "rtgs",
        "settlement", "t+1", "t+2", "cross-border", "faster payments",
        "iso 20022", "treasury", "liquidity", "cash management",
    ],
    "FX_and_Currency_Strategy": [
        "fx", "foreign exchange", "currency", "renminbi", "rmb",
        "dollar", "de-dollar", "dollarization", "swift",
    ],
    "Core_Banking_and_Lending_Modernization": [
        "core banking", "core", "lending", "loan", "credit", "t24",
        "temenos", "mambu", "zafin",
    ],
    "Compliance_Risk_and_Standards": [
        "regulation", "regulatory", "compliance", "aml", "kyc", "sanction",
        "financial crime", "risk", "dora", "mica", "psd", "law", "act",
        "guideline", "policy", "supervision", "basel", "fsb", "finma",
        "occ", "fca", "notice",
    ],
    "Market_Research_and_Fintech_Landscapes": [
        "report", "outlook", "survey", "landscape", "trends", "benchmark",
        "market", "state of", "year in review", "adoption", "fintech map",
    ],
    "AI_and_Digital_Transformation": [
        "ai", "artificial intelligence", "genai", "machine learning",
        "data governance", "digital transformation", "automation", "agentic",
        "llm", "claude", "copilot",
    ],
}

ACADEMIC_HINTS = [
    "working paper", "journal", "research series", "ssrn", "university",
    "institute", "law & justice", "forthcoming",
]

REPORT_HINTS = [
    "report", "outlook", "survey", "review", "trends", "study",
    "white paper", "technical note", "guide", "handbook",
]

GENERIC_SUBFOLDERS = {
    "Academic",
    "Industry",
    "Reports",
    "Independent",
    "Unknown",
    "Regulation",
}

# Common organization aliases used for publisher detection.
ORG_ALIASES = {
    "bank for international settlements": "BIS",
    "bis": "BIS",
    "international monetary fund": "IMF",
    "imf": "IMF",
    "european central bank": "ECB",
    "ecb": "ECB",
    "bank of england": "Bank of England",
    "world bank": "World Bank",
    "international bank for reconstruction and development": "World Bank",
    "swift": "SWIFT",
    "visa": "Visa",
    "mastercard": "Mastercard",
    "pwc": "PwC",
    "bank of canada": "Bank of Canada",
    "sequoia": "Sequoia Capital",
    "sequoia capital": "Sequoia Capital",
    "s&p global": "S&P Global Ratings",
    "s&p global ratings": "S&P Global Ratings",
    "federal reserve": "Federal Reserve",
    "cpmi": "CPMI",
    "oecd": "OECD",
    "wef": "WEF",
    "world economic forum": "WEF",
}

TAG_RULES = {
    "payments": [
        "payment", "payments", "rtgs", "instant", "real-time", "realtime",
        "faster payments", "settlement", "treasury", "liquidity",
    ],
    "stablecoins": ["stablecoin", "stablecoins"],
    "tokenization": ["tokenization", "tokenised", "tokenized", "security token"],
    "crypto": ["crypto", "cryptoasset", "crypto asset", "digital asset"],
    "regulation": ["regulation", "regulatory", "guidance", "act", "directive", "law"],
    "policy": ["policy"],
    "iso20022": ["iso 20022", "iso20022"],
    "cross-border": ["cross-border", "cross border"],
    "digital identity": ["digital id", "digital identity", "vlei"],
    "t+1": ["t+1"],
    "settlement": ["settlement"],
    "ai": ["artificial intelligence", " ai ", "machine learning", "llm", "agentic", "genai"],
    "genai": ["genai", "generative ai"],
    "data": ["data governance", "data strategy", "data management"],
    "market research": ["outlook", "survey", "year in review", "trends", "state of"],
    "fintech": ["fintech"],
    "adoption": ["adoption"],
    "benchmark": ["benchmark"],
    "risk": ["risk"],
    "security": ["security"],
    "compliance": ["compliance", "aml", "kyc"],
    "financial crime": ["financial crime", "illicit", "tbml"],
    "tokenised deposits": ["tokenised deposit", "tokenized deposit"],
    "uk": ["united kingdom", " uk "],
    "us": ["united states", " us "],
    "eu": ["european union", " eu "],
    "belgium": ["belgium"],
    "asean": ["asean"],
    "mena": ["mena", "middle east"],
    "latin america": ["latin america"],
    "bis": ["bis", "bank for international settlements"],
    "imf": ["imf", "international monetary fund"],
    "visa": ["visa"],
    "federal reserve": ["federal reserve"],
}

MONTHS = {
    "january": "Jan",
    "jan": "Jan",
    "february": "Feb",
    "feb": "Feb",
    "march": "Mar",
    "mar": "Mar",
    "april": "Apr",
    "apr": "Apr",
    "may": "May",
    "june": "Jun",
    "jun": "Jun",
    "july": "Jul",
    "jul": "Jul",
    "august": "Aug",
    "aug": "Aug",
    "september": "Sep",
    "sep": "Sep",
    "october": "Oct",
    "oct": "Oct",
    "november": "Nov",
    "nov": "Nov",
    "december": "Dec",
    "dec": "Dec",
}


def log(msg: str) -> None:
    print(msg)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_filename(name: str) -> str:
    base = name.strip()
    base = base.replace("_", " ")
    base = re.sub(r"\s+", " ", base)
    base = re.sub(r"\s*\((\d+)\)$", "", base)
    base = base.replace("/", "-")
    base = re.sub(r"\s+\.", ".", base)
    base = base.strip()
    if base.lower().endswith(".pdf"):
        base = base[:-4] + ".pdf"
    else:
        base = base + ".pdf"
    return base


def extract_pdf_bundle(path: Path, max_pages: int = 3) -> Tuple[str, List[str], Dict[str, str]]:
    try:
        reader = PyPDF2.PdfReader(str(path))
    except Exception:
        return "", [], {}

    meta = {}
    try:
        meta = reader.metadata or {}
    except Exception:
        meta = {}

    text_parts: List[str] = []
    for i in range(min(max_pages, len(reader.pages))):
        try:
            text_parts.append(reader.pages[i].extract_text() or "")
        except Exception:
            continue
    raw_text = "\n".join(text_parts)
    clean_text = " ".join(raw_text.split())
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    return clean_text, lines, meta


def is_generic_title(text: str) -> bool:
    if not text:
        return True
    stripped = text.strip()
    if len(stripped) < 6:
        return True
    if not re.search(r"[A-Za-z]", stripped):
        return True
    lowered = stripped.lower()
    if lowered.startswith("microsoft word") or lowered.startswith("adobe"):
        return True
    if lowered.startswith("untitled") or lowered.startswith("document"):
        return True
    return False


def is_bad_title_line(text: str) -> bool:
    lowered = text.lower()
    bad_fragments = [
        "disclaimer",
        "all rights reserved",
        "copyright",
        "table of contents",
        "contents",
        "version",
        "draft",
        "confidential",
        "links from this document",
        "accepts no responsibility",
        "no responsibility",
        "liability",
        "proceeding to read",
        "terms",
        "best endeavours",
        "www.",
        "http",
    ]
    if any(fragment in lowered for fragment in bad_fragments):
        return True
    if re.fullmatch(r"\d+", text.strip()):
        return True
    if re.fullmatch(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\\s+20\\d{2}", lowered):
        return True
    if len(text) > 160:
        return True
    return False


def clean_title(text: str) -> str:
    title = text.strip()
    title = title.replace("_", " ")
    title = re.sub(r"\s+", " ", title)
    title = title.replace("\u2013", "-").replace("\u2014", "-")
    title = title.strip(" -_")
    return title


def pick_title(filename: str, lines: List[str], meta: Dict[str, str]) -> str:
    meta_title = clean_title(str(meta.get("/Title", "") or ""))
    if meta_title and not is_generic_title(meta_title):
        return meta_title

    # Prefer the first good-looking line.
    for line in lines[:10]:
        candidate = clean_title(line)
        if is_generic_title(candidate) or is_bad_title_line(candidate):
            continue
        if 6 <= len(candidate) <= 140:
            return candidate

    # Try best line from the first page(s).
    best_line = ""
    best_score = 0
    for line in lines[:20]:
        candidate = clean_title(line)
        if is_generic_title(candidate) or is_bad_title_line(candidate):
            continue
        alpha_count = len(re.findall(r"[A-Za-z]", candidate))
        score = alpha_count
        if 10 <= len(candidate) <= 140:
            score += 10
        if score > best_score:
            best_score = score
            best_line = candidate
    if best_line:
        return best_line

    # Fallback to filename stem.
    stem = clean_title(Path(filename).stem)
    return stem if stem else filename


def infer_date(text: str, filename: str) -> Tuple[Optional[str], Optional[str]]:
    haystack = f"{filename} {text}".lower()

    # ISO-like date: 2026-03-05 or 2026/03/05
    m = re.search(r"\b(20\d{2})[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])\b", haystack)
    if m:
        year = m.group(1)
        month_num = int(m.group(2))
        month = calendar.month_abbr[month_num]
        return f"{month} {year}", year

    # Month name + year
    month_names = "|".join(sorted(MONTHS.keys(), key=len, reverse=True))
    m = re.search(rf"\b({month_names})\b\s*(20\d{{2}})", haystack)
    if m:
        month = MONTHS[m.group(1)]
        year = m.group(2)
        return f"{month} {year}", year

    # Year only (pick the most recent)
    years = [int(y) for y in re.findall(r"\b(20\d{2})\b", haystack)]
    if years:
        year = str(max(years))
        return None, year

    return None, None


def infer_publisher(filename: str, text: str, meta: Dict[str, str], subfolder: str) -> str:
    # If filename already has a publisher-style prefix, keep it.
    if " - " in filename:
        prefix = clean_title(filename.split(" - ", 1)[0])
        if prefix and not is_generic_title(prefix):
            return prefix

    # Use subfolder if it's a specific organization.
    if subfolder and subfolder not in GENERIC_SUBFOLDERS:
        return clean_title(subfolder.replace("_", " "))

    # Try metadata author.
    author = clean_title(str(meta.get("/Author", "") or ""))
    if author and not is_generic_title(author):
        return author

    # Search text for known org aliases.
    haystack = f"{filename} {text}".lower()
    for key, value in ORG_ALIASES.items():
        if key in haystack:
            return value

    return ""


def build_filename(title: str, publisher: str, date_mon_year: Optional[str], year: Optional[str]) -> str:
    base_title = clean_title(title)
    if publisher:
        if base_title.lower().startswith(publisher.lower() + " - "):
            base_title = base_title[len(publisher) + 3 :]
        base = f"{publisher} - {base_title}" if base_title else publisher
    else:
        base = base_title

    suffix = ""
    if date_mon_year and date_mon_year.lower() not in base.lower():
        suffix = f" ({date_mon_year})"
    elif year and year not in base:
        suffix = f" ({year})"

    return normalize_filename(base + suffix)


def split_sentences(text: str) -> List[str]:
    if not text:
        return []
    cleaned = re.sub(r"\s+", " ", text).strip()
    # Simple sentence split.
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", cleaned)
    sentences = [p.strip() for p in parts if p.strip()]
    return sentences


def generate_summary(text: str, title: str, lines: Optional[List[str]] = None) -> str:
    title_clean = clean_title(title)
    sentences = split_sentences(text)

    filtered: List[str] = []
    for s in sentences:
        cleaned = clean_title(s)
        if not cleaned:
            continue
        if is_bad_title_line(cleaned):
            continue
        if title_clean and cleaned.lower().startswith(title_clean.lower()):
            continue
        filtered.append(cleaned)
        if len(filtered) >= 2:
            break

    if not filtered and lines:
        # Fallback to cleaned lines when sentence split fails.
        for line in lines:
            cleaned = clean_title(line)
            if not cleaned:
                continue
            if is_bad_title_line(cleaned):
                continue
            if title_clean and cleaned.lower().startswith(title_clean.lower()):
                continue
            filtered.append(cleaned)
            if len(filtered) >= 2:
                break

    if filtered:
        summary = " ".join(filtered).strip()
        if summary and summary[-1] not in ".!?":
            summary += "."
        # Keep summaries reasonably short.
        if len(summary) > 260:
            cutoff = summary.rfind(".", 0, 260)
            if cutoff > 80:
                summary = summary[: cutoff + 1]
            else:
                summary = summary[:260].rstrip() + "..."

        # Bail out if summary still looks like a disclaimer.
        bad_fragments = [
            "errors or omissions",
            "liability",
            "responsibility",
            "disclaimer",
            "terms",
            "proceeding to read",
            "all rights reserved",
        ]
        lowered = summary.lower()
        if any(bad in lowered for bad in bad_fragments):
            summary = ""

        word_count = len([w for w in re.split(r"\\s+", summary) if w])
        if word_count < 6:
            summary = ""

        if summary:
            return summary

    fallback = clean_title(title)
    if not fallback:
        return "Brief summary not available."

    lower_title = fallback.lower()
    if "guide" in lower_title or "handbook" in lower_title:
        return f"Guide on {fallback}."
    if "report" in lower_title or "survey" in lower_title:
        return f"Report on {fallback}."
    return f"Brief on {fallback}."


def generate_tags(text: str, title: str, category: str, subfolder: str) -> List[str]:
    haystack = f" {title} {text} {category} {subfolder} ".lower()
    tags: List[str] = []
    for tag, keywords in TAG_RULES.items():
        for kw in keywords:
            if kw in haystack:
                tags.append(tag)
                break

    # Category-driven tags
    if category == "Payments_RealTime_and_Liquidity" and "payments" not in tags:
        tags.append("payments")
    if category == "Stablecoins_and_CBDC" and "stablecoins" not in tags:
        tags.append("stablecoins")
    if category == "Tokenization_Blockchain_and_Digital_Assets" and "tokenization" not in tags:
        tags.append("tokenization")
    if category == "Compliance_Risk_and_Standards" and "regulation" not in tags:
        tags.append("regulation")
    if category == "AI_and_Digital_Transformation" and "ai" not in tags:
        tags.append("ai")

    # Keep tags unique and capped.
    unique = []
    for t in tags:
        if t not in unique:
            unique.append(t)
    return unique[:5]


def classify_category(text: str, filename: str) -> Tuple[str, int]:
    haystack = f"{filename} {text}".lower()
    best_category = ""
    best_score = 0
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in haystack:
                score += 1
        if score > best_score:
            best_category = category
            best_score = score
    return best_category, best_score


def build_subfolder_map(category_path: Path) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    if not category_path.exists():
        return mapping
    for child in category_path.iterdir():
        if not child.is_dir():
            continue
        key = re.sub(r"[^a-z0-9]+", " ", child.name.lower()).strip()
        mapping[key] = child.name
    return mapping


def pick_subfolder(category: str, text: str, filename: str) -> str:
    category_path = ROOT / category
    subfolders = build_subfolder_map(category_path)

    haystack = f"{filename} {text}".lower()
    normalized_haystack = re.sub(r"[^a-z0-9]+", " ", haystack)

    # Prefer explicit subfolder name matches.
    for key, folder in subfolders.items():
        if key and key in normalized_haystack:
            return folder

    # Heuristic fallback.
    if any(hint in haystack for hint in ACADEMIC_HINTS) and "Academic" in subfolders.values():
        return "Academic"
    if any(hint in haystack for hint in REPORT_HINTS) and "Reports" in subfolders.values():
        return "Reports"
    if "Industry" in subfolders.values():
        return "Industry"
    if "Reports" in subfolders.values():
        return "Reports"

    # Default to first available subfolder, or create Reports.
    if subfolders:
        return sorted(subfolders.values())[0]
    return "Reports"


def ensure_unique_path(dest: Path) -> Path:
    if not dest.exists():
        return dest
    stem = dest.stem
    suffix = dest.suffix
    parent = dest.parent
    i = 2
    while True:
        candidate = parent / f"{stem} ({i}){suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def move_or_copy(src: Path, dest: Path) -> bool:
    """Move src to dest; if move isn't permitted, copy and try to delete src.
    Returns True if src was removed, False otherwise.
    """
    try:
        shutil.move(str(src), str(dest))
        return True
    except PermissionError:
        # Fall back to copy if source is in a protected location (e.g., CloudStorage).
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        try:
            src.unlink()
            return True
        except PermissionError:
            log(f"WARN: Could not remove source file: {src}")
            return False


def load_state(state_path: Path) -> Dict[str, str]:
    if not state_path.exists():
        return {}
    try:
        return json.loads(state_path.read_text())
    except Exception:
        return {}


def save_state(state_path: Path, state: Dict[str, str]) -> None:
    state_path.write_text(json.dumps(state, indent=2))


def should_run_schedule(state_path: Path) -> bool:
    state = load_state(state_path)
    last_run = state.get("last_run")
    if not last_run:
        return True
    try:
        last_dt = datetime.fromisoformat(last_run)
    except ValueError:
        return True
    return datetime.now() - last_dt >= timedelta(hours=48)


def record_run(state_path: Path) -> None:
    state = load_state(state_path)
    state["last_run"] = datetime.now().isoformat(timespec="seconds")
    save_state(state_path, state)


def apply_catalog_updates(updates: List[Dict]) -> None:
    if not updates:
        return
    catalog_path = ROOT / "scripts" / "catalog.json"
    if catalog_path.exists():
        try:
            entries = json.loads(catalog_path.read_text())
        except Exception:
            entries = []
    else:
        entries = []

    index = {entry.get("path"): entry for entry in entries if entry.get("path")}

    for upd in updates:
        path = upd.get("path")
        if not path:
            continue
        entry = index.get(path)
        if not entry:
            entry = {
                "path": path,
                "title": upd.get("title", Path(path).stem),
                "summary": upd.get("summary", ""),
                "tags": upd.get("tags", []),
            }
            entries.append(entry)
            index[path] = entry
            continue

        if not entry.get("title"):
            entry["title"] = upd.get("title", Path(path).stem)
        if not entry.get("summary"):
            entry["summary"] = upd.get("summary", "")

        existing_tags = entry.get("tags", []) or []
        combined: List[str] = []
        for t in existing_tags + (upd.get("tags", []) or []):
            if t not in combined:
                combined.append(t)
        entry["tags"] = combined

    entries = sorted(entries, key=lambda e: e.get("path", ""))
    catalog_path.write_text(json.dumps(entries, indent=2))


def collect_repo_hashes() -> Dict[str, Path]:
    hashes: Dict[str, Path] = {}
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() != ".pdf":
            continue
        if ".git" in path.parts or path.parts[0] == "docs":
            continue
        hashes[sha256(path)] = path
    return hashes


def iter_inbox_pdfs(inbox: Path) -> List[Path]:
    pdfs: List[Path] = []
    for path in inbox.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() != ".pdf":
            continue
        if "_processed" in path.parts:
            continue
        pdfs.append(path)
    return sorted(pdfs)


def iter_inbox_zips(inbox: Path) -> List[Path]:
    zips: List[Path] = []
    for path in inbox.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() != ".zip":
            continue
        if "_processed" in path.parts:
            continue
        zips.append(path)
    return sorted(zips)


def process_pdf(
    source: Path,
    repo_hashes: Dict[str, Path],
    seen_hashes: set,
    duplicates_dir: Path,
    review_dir: Path,
    dry_run: bool,
    catalog_updates: List[Dict],
    source_name: Optional[str] = None,
) -> Tuple[str, Optional[Path]]:
    """Process a single PDF. Returns (status, destination_path)."""
    name_for_analysis = source_name or source.name
    file_hash = sha256(source)
    if file_hash in repo_hashes or file_hash in seen_hashes:
        dest = duplicates_dir / f"{Path(name_for_analysis).stem}__dup_{file_hash[:8]}.pdf"
        dest = ensure_unique_path(dest)
        if not dry_run:
            move_or_copy(source, dest)
        return "duplicate", dest

    text, lines, meta = extract_pdf_bundle(source)
    category, score = classify_category(text, name_for_analysis)
    if not category or score == 0:
        dest = review_dir / normalize_filename(name_for_analysis)
        dest = ensure_unique_path(dest)
        if not dry_run:
            move_or_copy(source, dest)
        return "review", dest

    subfolder = pick_subfolder(category, text, name_for_analysis)
    dest_dir = ROOT / category / subfolder
    title = pick_title(name_for_analysis, lines, meta)
    date_mon_year, year = infer_date(text, name_for_analysis)
    publisher = infer_publisher(name_for_analysis, text, meta, subfolder)
    dest_name = build_filename(title, publisher, date_mon_year, year)
    dest = ensure_unique_path(dest_dir / dest_name)

    if not dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)
        move_or_copy(source, dest)

    summary = generate_summary(text, title, lines)
    tags = generate_tags(text, title, category, subfolder)
    try:
        rel_path = str(dest.relative_to(ROOT))
    except ValueError:
        rel_path = ""
    if rel_path:
        catalog_updates.append(
            {
                "path": rel_path,
                "title": clean_title(Path(dest_name).stem),
                "summary": summary,
                "tags": tags,
            }
        )

    seen_hashes.add(file_hash)
    return "added", dest


def process_zip(
    zip_path: Path,
    repo_hashes: Dict[str, Path],
    seen_hashes: set,
    duplicates_dir: Path,
    review_dir: Path,
    processed_dir: Path,
    dry_run: bool,
    catalog_updates: List[Dict],
) -> Tuple[int, int, int]:
    added = duplicates = review = 0
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_root = Path(tmp_dir)
        try:
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(tmp_root)
        except zipfile.BadZipFile:
            log(f"WARN: bad zip, skipping: {zip_path}")
            return added, duplicates, review

        for pdf in tmp_root.rglob("*"):
            if not pdf.is_file():
                continue
            if pdf.suffix.lower() != ".pdf":
                continue
            # Copy to temp location we can move from
            staged = tmp_root / f"_staged_{pdf.name}"
            shutil.copy2(pdf, staged)
            status, _ = process_pdf(
                staged,
                repo_hashes,
                seen_hashes,
                duplicates_dir,
                review_dir,
                dry_run,
                catalog_updates,
                source_name=pdf.name,
            )
            if status == "added":
                added += 1
            elif status == "duplicate":
                duplicates += 1
            else:
                review += 1

    # Move processed zip
    dest = processed_dir / zip_path.name
    dest = ensure_unique_path(dest)
    if not dry_run:
        processed_dir.mkdir(parents=True, exist_ok=True)
        move_or_copy(zip_path, dest)

    return added, duplicates, review


def main() -> int:
    parser = argparse.ArgumentParser(description="Intake PDFs from inbox into repo")
    parser.add_argument("--inbox", type=Path, default=DEFAULT_INBOX)
    parser.add_argument("--duplicates", type=Path, default=DEFAULT_DUPLICATES)
    parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--processed", type=Path, default=DEFAULT_INBOX / "_processed")
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--schedule", action="store_true", help="enforce 48h cadence")
    parser.add_argument("--force", action="store_true", help="override schedule guard")
    args = parser.parse_args()

    inbox = args.inbox
    duplicates_dir = args.duplicates
    review_dir = args.review
    processed_dir = args.processed
    state_path = args.state

    inbox.mkdir(parents=True, exist_ok=True)
    duplicates_dir.mkdir(parents=True, exist_ok=True)
    review_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    if args.schedule and not args.force:
        if not should_run_schedule(state_path):
            log("Schedule guard: last run < 48h, skipping.")
            return 0

    repo_hashes = collect_repo_hashes()
    seen_hashes: set = set()

    added = duplicates = review = 0
    catalog_updates: List[Dict] = []

    pdfs = iter_inbox_pdfs(inbox)
    zips = iter_inbox_zips(inbox)

    if not pdfs and not zips:
        log("Inbox empty. Nothing to do.")
        return 0

    log(f"Found {len(pdfs)} PDFs and {len(zips)} ZIPs in inbox.")

    for pdf in pdfs:
        status, dest = process_pdf(
            pdf,
            repo_hashes,
            seen_hashes,
            duplicates_dir,
            review_dir,
            args.dry_run,
            catalog_updates,
        )
        if status == "added":
            added += 1
        elif status == "duplicate":
            duplicates += 1
        else:
            review += 1
        if dest:
            log(f"{status.upper()}: {pdf.name} -> {dest}")

    for zip_path in zips:
        a, d, r = process_zip(
            zip_path,
            repo_hashes,
            seen_hashes,
            duplicates_dir,
            review_dir,
            processed_dir,
            args.dry_run,
            catalog_updates,
        )
        added += a
        duplicates += d
        review += r

    if added > 0 and not args.dry_run:
        apply_catalog_updates(catalog_updates)
        log("Updating catalog...")
        subprocess.run([sys.executable, str(ROOT / "scripts" / "build_catalog.py")], check=True)

    if args.schedule and not args.dry_run:
        record_run(state_path)

    log(f"Done. Added={added}, Duplicates={duplicates}, Review={review}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
