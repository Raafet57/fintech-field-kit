# Schema Map — Phase 1

Conservative JSON-LD plan. Add schema only where visible page content supports the claim.

## Global Person object seed

Use on home/about and as `author`/`creator` reference on posts/projects.

```json
{
  "@type": "Person",
  "@id": "https://raafetchoukri.com/#person",
  "name": "Raafet Choukri",
  "url": "https://raafetchoukri.com/",
  "jobTitle": "Independent Payments and Fintech Consultant",
  "knowsAbout": [
    "SWIFTRef",
    "ISO 20022",
    "Payment reference data",
    "BIC",
    "IBAN",
    "LEI",
    "Settlement instructions",
    "Payment pre-validation",
    "Verification of Payee",
    "Cross-border payments",
    "vLEI",
    "Digital identity",
    "Fintech product strategy"
  ],
  "knowsLanguage": ["English", "French", "Arabic"],
  "homeLocation": {
    "@type": "Place",
    "name": "Singapore"
  }
}
```

Add `sameAs` links only if the exact public profile URLs are approved and visible on the page.

## Home
Types:
- `WebSite`
- `Person`
- Optional `ProfessionalService` if services are visible on page.

## About
Types:
- `ProfilePage`
- `Person`
- `BreadcrumbList`

## Services overview
Types:
- `WebPage`
- `ProfessionalService`
- `BreadcrumbList`

Do not imply regulated financial service provider status. This is consulting/advisory/implementation support, not a bank/FMI/payment institution claim.

## Service detail pages
Types:
- `Service`
- `WebPage`
- `BreadcrumbList`

Example service areas:
- SWIFTRef/reference-data integration
- ISO 20022 migration/data quality
- Payment pre-validation/PPC/VOP
- Payment reference-data automation
- Payments product strategy

## Posts
Types:
- `BlogPosting` or `Article`
- `BreadcrumbList`

Fields:
- headline
- description/excerpt
- datePublished
- dateModified if available
- author: `https://raafetchoukri.com/#person`
- mainEntityOfPage
- keywords from tags

## Library index
Types:
- `CollectionPage`
- `ItemList` for selected/top visible records, not necessarily all 339 in one JSON-LD block.
- `BreadcrumbList`

## Library detail pages
Types:
- `CreativeWork` or `DigitalDocument`
- `BreadcrumbList`

Fields where available:
- name/headline
- description
- keywords/tags
- url
- associatedMedia or encoding for PDF URL only if safe and stable
- publisher/source institution only if data field exists; do not infer from noisy titles.

## Topic pages
Types:
- `CollectionPage`
- `ItemList`
- `BreadcrumbList`

Add `about`/`keywords` based on topic slug/name.

## Projects index
Types:
- `CollectionPage`
- `ItemList`
- `BreadcrumbList`

## vLEI project detail
Types:
- `CreativeWork` by default.
- Use `SoftwareApplication` only if visible copy clearly presents it as a software demo/application and does not imply production readiness.
- `BreadcrumbList`.

Required boundary text visible on page and optionally in schema description:
- reference demo
- sanitized/curated fixtures
- demonstrates identity proof -> policy decision -> verdict/evidence/audit flow
- does not claim production readiness or live-vLEI verification by default

Avoid:
- production financial infrastructure claims
- live verification claims unless backed by live configured KERIA/vLEI evidence
- client/customer claims
- regulated payment service claims

## FAQPage
Only use where the page visibly renders matching FAQ questions and answers. Do not add invisible FAQ schema.
