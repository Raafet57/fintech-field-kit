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


def extract_text(path: Path, max_pages: int = 2) -> str:
    try:
        reader = PyPDF2.PdfReader(str(path))
    except Exception:
        return ""
    text_parts: List[str] = []
    for i in range(min(max_pages, len(reader.pages))):
        try:
            text_parts.append(reader.pages[i].extract_text() or "")
        except Exception:
            continue
    text = " ".join(text_parts)
    return " ".join(text.split())


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
) -> Tuple[str, Optional[Path]]:
    """Process a single PDF. Returns (status, destination_path)."""
    file_hash = sha256(source)
    if file_hash in repo_hashes or file_hash in seen_hashes:
        dest = duplicates_dir / f"{source.stem}__dup_{file_hash[:8]}.pdf"
        dest = ensure_unique_path(dest)
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(dest))
        return "duplicate", dest

    text = extract_text(source)
    category, score = classify_category(text, source.name)
    if not category or score == 0:
        dest = review_dir / normalize_filename(source.name)
        dest = ensure_unique_path(dest)
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(dest))
        return "review", dest

    subfolder = pick_subfolder(category, text, source.name)
    dest_dir = ROOT / category / subfolder
    dest_name = normalize_filename(source.name)
    dest = ensure_unique_path(dest_dir / dest_name)

    if not dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(dest))

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

        for pdf in tmp_root.rglob("*.pdf"):
            if not pdf.is_file():
                continue
            # Copy to temp location we can move from
            staged = tmp_root / f"_staged_{pdf.name}"
            shutil.copy2(pdf, staged)
            status, _ = process_pdf(staged, repo_hashes, seen_hashes, duplicates_dir, review_dir, dry_run)
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
        shutil.move(str(zip_path), str(dest))

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

    pdfs = iter_inbox_pdfs(inbox)
    zips = iter_inbox_zips(inbox)

    if not pdfs and not zips:
        log("Inbox empty. Nothing to do.")
        return 0

    log(f"Found {len(pdfs)} PDFs and {len(zips)} ZIPs in inbox.")

    for pdf in pdfs:
        status, dest = process_pdf(pdf, repo_hashes, seen_hashes, duplicates_dir, review_dir, args.dry_run)
        if status == "added":
            added += 1
        elif status == "duplicate":
            duplicates += 1
        else:
            review += 1
        if dest:
            log(f"{status.upper()}: {pdf.name} -> {dest}")

    for zip_path in zips:
        a, d, r = process_zip(zip_path, repo_hashes, seen_hashes, duplicates_dir, review_dir, processed_dir, args.dry_run)
        added += a
        duplicates += d
        review += r

    if added > 0 and not args.dry_run:
        log("Updating catalog...")
        subprocess.run([sys.executable, str(ROOT / "scripts" / "build_catalog.py")], check=True)

    if args.schedule and not args.dry_run:
        record_run(state_path)

    log(f"Done. Added={added}, Duplicates={duplicates}, Review={review}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
