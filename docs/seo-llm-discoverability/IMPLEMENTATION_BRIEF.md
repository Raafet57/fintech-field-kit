# raafetchoukri.com SEO + LLM Discoverability — Phase 1 Replit Implementation Brief

> For Replit AI: implement this in the website project. Keep changes surgical. Do **not** change deployment, secrets, paid services, analytics, Search Console/Bing, or production data. Do **not** alter robots.txt crawler policy unless Raf explicitly provides a separate decision.

## Goal
Make raafetchoukri.com machine-readable and citation-friendly for search engines, LLM retrieval, link previews, and high-intent industry discovery while preserving Raf's claim boundaries.

## Website model to preserve
The site is not only a consultant homepage. It has five surfaces:

1. **Library** — curated industry intelligence / source catalogue / reference shelf.
2. **Posts & Insights** — Raf-authored analysis and blog-style interpretation.
3. **Projects** — live demos and proof-of-work, currently including vLEI Auth Platform.
4. **Topics** — taxonomy/navigation layer across payments, ISO 20022, SWIFT, SSI, vLEI, AI, regulation, etc.
5. **Services/About/Contact** — commercial conversion and Raf entity clarity.

## Current live audit findings to fix
From live audit on 2026-05-22:

- Sitemap has 505 URLs: 340 Library, 64 Posts, 97 Topics, 2 Projects, homepage, privacy.
- Raw HTML for representative routes is a shared React/Vite SPA shell with `<div id="root"></div>` and generic title/meta.
- `/llms.txt` returns the HTML shell, not a text/markdown LLM guide.
- Unknown routes return 200 with the SPA shell (soft-404).
- No canonical tags observed.
- No JSON-LD observed.
- OG metadata is generic and missing `og:url`/`og:image`; Twitter tags absent.
- `robots.txt` currently blocks GPTBot, ChatGPT-User, CCBot, Google-Extended, anthropic-ai, and ClaudeBot. **Do not change this without Raf approval.**

## Implementation constraints

- Prefer minimal implementation inside the current Replit app.
- If full SSR/SSG migration is too large, implement the smallest route-aware server/meta/prerender layer that makes representative public routes return useful raw HTML.
- Preserve current visual UI and content. This phase is about discoverability, not redesign.
- Keep vLEI public demo boundaries: reference demo, sanitized fixtures, not production readiness, not live-vLEI verification by default.
- Use existing data arrays/content sources if present; do not duplicate large content manually unless needed for generated HTML/meta.

## Phase 1 acceptance criteria

### A. `/llms.txt`
- `GET /llms.txt` returns `200` with `Content-Type: text/plain` or `text/markdown`.
- It returns the content in `LLMS_TXT_DRAFT.md` or equivalent updated copy.
- It must not return HTML or the SPA shell.

### B. Route-specific metadata
Representative routes must have unique raw HTML title/meta/canonical/OG/Twitter where possible:

- `/`
- `/library`
- `/library/the-role-of-iso-20022`
- `/posts/vlei-auth-platform-launch`
- `/topics/iso20022`
- `/projects`
- `/projects/vlei-auth-platform`
- `/about` if created
- `/services` if created

Minimum per route:

```html
<title>...</title>
<meta name="description" content="..." />
<link rel="canonical" href="https://raafetchoukri.com/..." />
<meta property="og:title" content="..." />
<meta property="og:description" content="..." />
<meta property="og:type" content="website|article" />
<meta property="og:url" content="https://raafetchoukri.com/..." />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="..." />
<meta name="twitter:description" content="..." />
```

### C. JSON-LD schema
Add raw HTML JSON-LD for representative routes:

- Home/About: `Person` + `WebSite` (+ `ProfessionalService` only if supported by visible copy).
- Posts: `BlogPosting` or `Article` + `BreadcrumbList`.
- Library index/topic pages: `CollectionPage` or `ItemList`.
- Library detail pages: `CreativeWork` / `DigitalDocument` style schema where source fields exist.
- Projects: `CreativeWork` or `SoftwareApplication` only if not overclaiming.
- Use `FAQPage` only if visible FAQ content exists on the page.

### D. Raw HTML content / crawlability
For representative public routes, `curl` should show route-specific content, not just an empty app shell. Minimum acceptable fallback if full prerender is not ready:

- route-specific H1
- route-specific summary/description
- key internal links
- JSON-LD
- canonical/meta

Do not break the client-side app.

### E. 404/canonical behavior
- Unknown public routes return `404` or `410`, not `200` SPA shell.
- Choose one URL style (recommend no trailing slash except `/`) and enforce via canonical tags or redirects.

## Preferred implementation sequence

### Task 1 — Locate route/data sources
Find where the app defines:

- posts data
- library/catalog data or API usage
- project data
- topics route
- Express/server routes or static fallback
- current `index.html` template
- robots/sitemap generation

Do not edit yet. Summarize exact files before making changes.

### Task 2 — Add real `/llms.txt`
Use `LLMS_TXT_DRAFT.md`. Implement as a static file or explicit server route that bypasses SPA fallback.

Expected check:

```bash
curl -i https://raafetchoukri.com/llms.txt | head -40
```

Expected:

```txt
HTTP/2 200
content-type: text/plain or text/markdown
# Raafet Choukri
```

### Task 3 — Add metadata builder
Create a route metadata map/function for:

- home
- library index
- library detail
- posts index
- post detail
- topics index
- topic detail
- projects index
- vLEI project detail
- about
- services
- privacy

Use `ROUTE_METADATA_MATRIX.md` as seed copy.

### Task 4 — Add schema builder
Create a route schema map/function. Use `SCHEMA_MAP.md`. Keep schema conservative; never claim production capability for demos.

### Task 5 — Add raw route content/prerender fallback
If full SSR/SSG is not available, add server-generated HTML snippets for public route requests before serving the client app. The rendered client app can still hydrate/replace as normal, but crawlers should see meaningful H1/summary/internal links.

Minimum route snippets:

- Home: Raf entity + service summary + links to Library/Posts/Projects/Services.
- Library: curated reference shelf summary + top category links + selected document links.
- Library detail: title, summary, tags, PDF/source link if available.
- Post detail: title, date, excerpt/body starter, tags.
- Topic: topic name, description, links to matching Library/Post resources.
- Project vLEI: problem, proof shown, not claimed, demo link, related links.

### Task 6 — Fix soft-404
Ensure unknown routes not in known public route patterns return 404/410.

Valid dynamic patterns include:

- `/library/{slug}` only if slug exists
- `/posts/{slug}` only if slug exists
- `/topics/{slug}` only if slug exists
- `/projects/{slug}` only if slug exists

### Task 7 — Add `/about`, `/services`, and service page skeletons only if low-risk
If route setup is straightforward, add:

- `/about`
- `/services`
- `/services/swiftref-reference-data-integration`
- `/services/iso-20022-migration-data-quality`
- `/services/payment-pre-validation-ppc-vop`
- `/services/payment-reference-data-automation`
- `/services/payments-product-strategy`

If this is too large for Phase 1, create the metadata/schema routes and link placeholders, then stop and report.

### Task 8 — Verify
Run the commands in `VERIFICATION_CHECKLIST.md`.

## Stop conditions
Stop and ask Raf/Hari before doing any of these:

- Changing `robots.txt` AI crawler policy.
- Indexing `vlei.raafetchoukri.com` or changing its noindex posture.
- Making production-readiness claims about vLEI or other demos.
- Rewriting the service positioning beyond the route copy provided here.
- Migrating the whole app framework if a smaller prerender/server-meta fix works.
- Deployment/restart if Replit requires manual approval.

## Recommended first commit shape
If using GitHub commits, split as:

1. `docs: add SEO LLM implementation packet` (if committing these docs)
2. `feat: add llms.txt and route metadata`
3. `feat: add structured data and crawlable route fallbacks`
4. `fix: return 404 for unknown public routes`
5. `test: add crawlability checks`
