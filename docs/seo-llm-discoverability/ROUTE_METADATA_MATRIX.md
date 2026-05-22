# Route Metadata Matrix — Phase 1

Use this as seed copy. Adapt exact wording to existing site voice, but keep route-specific titles/descriptions in raw HTML.

| Route | Title | Meta description | og:type | Canonical |
|---|---|---|---|---|
| `/` | Raafet Choukri | SWIFTRef, ISO 20022 & Payment Reference Data Specialist | Independent payments and fintech specialist helping banks and fintechs with SWIFTRef integration, ISO 20022 data quality, EPC pre-validation, BIC/IBAN/LEI controls, and payment operations tooling. | website | `https://raafetchoukri.com/` |
| `/library` | Payments & Fintech Research Library | Raafet Choukri | Curated standards, rulebooks, market-structure papers, and industry research across SWIFT, EPC, ISO 20022, payments, stablecoins, AI, regulation, and digital assets. | website | `https://raafetchoukri.com/library` |
| `/posts` | Payments Insights & Posts | Raafet Choukri | Practitioner analysis on ISO 20022, SWIFT, SSI, payment pre-validation, stablecoins, digital identity, AI in finance, and cross-border payment operations. | website | `https://raafetchoukri.com/posts` |
| `/projects` | Projects & Reference Builds | Raafet Choukri | Live demos and reference builds showing Raf's payments, data-quality, digital-identity, and fintech infrastructure proof-of-work. | website | `https://raafetchoukri.com/projects` |
| `/topics` | Payments Topics | Raafet Choukri | Browse curated resources and insights by topic, including ISO 20022, SWIFT, SSI, vLEI, payments, compliance, stablecoins, AI, and digital identity. | website | `https://raafetchoukri.com/topics` |
| `/about` | About Raafet Choukri | Payments & Reference Data Specialist | About Raafet Choukri, an independent payments and fintech specialist based in Singapore with expertise in SWIFTRef, ISO 20022, reference data, and payment operations. | profile | `https://raafetchoukri.com/about` |
| `/services` | Payments & Reference Data Consulting Services | Raafet Choukri | Consulting services for SWIFTRef integration, ISO 20022 migration data quality, payment pre-validation, BIC/IBAN/LEI controls, and payment product strategy. | website | `https://raafetchoukri.com/services` |
| `/projects/vlei-auth-platform` | vLEI Auth Platform Reference Demo | Identity, Policy & Audit Evidence | Reference build demonstrating identity proof, policy decision, verdict, evidence, and audit flow for payment operations using sanitized fixtures. | website | `https://raafetchoukri.com/projects/vlei-auth-platform` |
| `/posts/vlei-auth-platform-launch` | vLEI Auth Platform: Identity Proof to Policy Decision to Audit Evidence | Raafet Choukri | Raf's launch note for the vLEI Auth Platform reference build: how identity, policy, verdicts, and audit evidence can support payment operations. | article | `https://raafetchoukri.com/posts/vlei-auth-platform-launch` |
| `/posts/from-static-ssis-to-digital-ssis` | From Static SSIs to Digital SSIs | Raafet Choukri | Analysis of how settlement instructions may evolve from static bank coordinates to digital wallet endpoints, identity, governance, and audit evidence. | article | `https://raafetchoukri.com/posts/from-static-ssis-to-digital-ssis` |
| `/topics/iso20022` | ISO 20022 Resources & Insights | Raafet Choukri | Curated ISO 20022 resources and Raf-authored insights covering migration, structured data, data quality, purpose codes, and payment operations. | website | `https://raafetchoukri.com/topics/iso20022` |
| `/topics/pre-validation` | Payment Pre-validation, PPC & VOP Resources | Raafet Choukri | Resources and insights on payment pre-validation, purpose/payment purpose codes, EPC Verification of Payee, beneficiary checks, and exception reduction. | website | `https://raafetchoukri.com/topics/pre-validation` |
| `/topics/swift` | SWIFT, SWIFTRef & Payment Reference Data Resources | Raafet Choukri | Resources and insights on SWIFT, SWIFTRef, BIC/IBAN/LEI data, settlement instructions, ISO 20022, and cross-border payment operations. | website | `https://raafetchoukri.com/topics/swift` |
| `/services/swiftref-reference-data-integration` | SWIFTRef & Payment Reference Data Integration Consulting | Raafet Choukri | Practitioner support for SWIFTRef portfolio integration, BIC Plus, IBAN Plus, BIC Directory, SSI Plus, Bankers World, and payment-reference-data quality. | website | `https://raafetchoukri.com/services/swiftref-reference-data-integration` |
| `/services/iso-20022-migration-data-quality` | ISO 20022 Migration & Data Quality Consulting | Raafet Choukri | Support for ISO 20022 migration, structured data, purpose codes, data-quality controls, exception reduction, and post-compliance operational value. | website | `https://raafetchoukri.com/services/iso-20022-migration-data-quality` |
| `/services/payment-pre-validation-ppc-vop` | Payment Pre-validation, PPC & VOP Consulting | Raafet Choukri | Help designing payment pre-validation, purpose-code, Verification of Payee, beneficiary-check, and repair-reduction operating models. | website | `https://raafetchoukri.com/services/payment-pre-validation-ppc-vop` |
| `/services/payment-reference-data-automation` | Payment Reference Data Automation | Raafet Choukri | Python, SQL, API, and ETL tooling for BIC/IBAN/LEI/SSI quality, routing data, sanctions inputs, onboarding controls, and audit trails. | website | `https://raafetchoukri.com/services/payment-reference-data-automation` |
| `/services/payments-product-strategy` | Payments Product Strategy & Market Positioning | Raafet Choukri | Product strategy, business-case, GTM, vendor/RFP, and market-positioning support for payments, reference-data, stablecoin, and fintech infrastructure teams. | website | `https://raafetchoukri.com/services/payments-product-strategy` |

## Dynamic route rules

### Posts
For `/posts/{slug}`:
- Title: `{post.title} | Raafet Choukri`
- Description: use `post.excerpt`, truncated to ~155 chars.
- og:type: `article`
- Add article published date and tags if available.

### Library detail
For `/library/{slug}`:
- Title: `{document.title} | Research Library | Raafet Choukri`
- Description: use `document.summary`, truncated to ~155 chars.
- og:type: `article` or `website`; prefer `article` only if using Article/CreativeWork schema.
- Include canonical URL and PDF/source link.

### Topics
For `/topics/{slug}`:
- Title: `{Topic Name} Resources & Insights | Raafet Choukri`
- Description: `Curated resources and insights on {topic} across payments, fintech infrastructure, standards, regulation, and operational controls.`
