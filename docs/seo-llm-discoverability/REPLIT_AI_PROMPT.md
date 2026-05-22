# Copy/Paste Prompt for Replit AI

You are implementing Phase 1 SEO + LLM discoverability for raafetchoukri.com.

Read these files first:

1. `docs/seo-llm-discoverability/IMPLEMENTATION_BRIEF.md`
2. `docs/seo-llm-discoverability/LLMS_TXT_DRAFT.md`
3. `docs/seo-llm-discoverability/ROUTE_METADATA_MATRIX.md`
4. `docs/seo-llm-discoverability/SCHEMA_MAP.md`
5. `docs/seo-llm-discoverability/VERIFICATION_CHECKLIST.md`

Implement the smallest safe change set that satisfies Phase 1:

- Real `/llms.txt` as text/plain or text/markdown, not SPA HTML.
- Route-specific title/meta/canonical/OG/Twitter for representative public routes.
- JSON-LD schema for home/about, posts, library, topics, projects where supported by visible content.
- Raw HTML should expose route-specific H1/summary/internal links for representative routes. If full SSR/SSG is too large, implement a route-aware server/prerender fallback without breaking client hydration.
- Unknown public routes should return 404/410, not 200 SPA shell.
- Preserve current visual design and content.
- Do not change `robots.txt` AI crawler policy unless Raf explicitly approves in a separate instruction.
- Keep vLEI demo as a reference demo with sanitized fixtures and no production/live-vLEI claim by default.

Before editing, summarize the exact files you found for route definitions, data sources, server fallback, index template, sitemap/robots/llms handling, and tests.

After implementation, run the checks in `VERIFICATION_CHECKLIST.md` and report exact outputs. Stop before deployment/restart if Replit asks for manual approval.
