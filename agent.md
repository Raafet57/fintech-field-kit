# Agent Playbook

This repository is a curated library of 2024–2025 fintech/digital money papers. When new files are added, follow this lightweight checklist.

## Workflow
- Scan for untracked PDFs and duplicate content hashes; keep organized copies in topic/institution folders.
- Remove redundant duplicates; prefer the existing organized file names.
- Normalize filenames for clarity (topic, issuer, year when obvious).
- Place each file under the right top-level folder: Stablecoins_and_CBDC, Tokenization_Blockchain_and_Digital_Assets, Payments_RealTime_and_Liquidity, FX_and_Currency_Strategy, Core_Banking_and_Lending_Modernization, Compliance_Risk_and_Standards, Market_Research_and_Fintech_Landscapes, AI_and_Digital_Transformation.
- Add/update `catalog.json` with a 1–2 sentence summary for each new paper (and tags if helpful).
- Regenerate catalog + README tree: `python scripts/build_catalog.py`.
- Stage, commit, and push once clean.

## Commands (local reminders)
- Find untracked: `git status -sb`
- Hash dupes: small Python one-liner (SHA-256 over repo, ignore .git)
- Build catalog/tree: `python scripts/build_catalog.py`
- After organizing: `git add ... && git commit -m "Organize new papers and clean duplicates" && git push`

## Naming hints
- Use source + short title + year where clear (e.g., `Visa - Global Payments and Fraud Report 2025.pdf`).
- Keep provenance words (IMF, BIS, WEF, OECD, KPMG, etc.) up front.
- Avoid `(1)` style suffixes; replace with descriptive titles instead.
