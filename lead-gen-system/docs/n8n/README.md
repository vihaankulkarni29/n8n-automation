# n8n Lead Generator Bot (Blueprint)

This blueprint defines a generalized n8n pipeline to ingest links/hashtags from multiple sources, normalize into a common schema, score brand readiness, optionally analyze via an AI model (Gemini), and persist JSON/CSV for review by rfrncs leadership. No outreach is sent by this pipeline.

## Workflow Outline
- Trigger: Email (IMAP) or Webhook containing a URL or hashtag.
- Detect Source: Function node determines `source_type` (yc, modemonline, justdial, instagram_hashtag, linkedin_hashtag, reddit, twitter, generic).
- Fetch & Parse: Route per source to fetch details (HTTP Request or scraper webhook). Minimal data pulled; heavy scraping handled by external scrapers when needed.
- Normalize: Function node maps raw fields to the common schema (see `schema/lead_entity.schema.json`).
- Score: Function node applies branding score rules (see `functions/scoring.js`).
- AI Analysis (optional): HTTP Request to Gemini with `prompts/brand_analysis_prompt.md` to classify brand maturity; output added to the lead JSON.
- Persist: Write daily JSON file and a CSV snapshot. Optionally upsert to Postgres.
- Notify: Email yourself a CSV snapshot for quick review.

## Nodes (suggested minimal set)
1. Trigger: Webhook OR IMAP Email
2. Function: Extract URL/hashtag + Detect source type
3. IF/Router: Branch by source type
4. HTTP Request (per source) OR Webhook call to existing scrapers
5. Function: Normalize (see `functions/normalize.js`)
6. Function: Score (see `functions/scoring.js`)
7. HTTP Request (AI) + Function (validate JSON) [optional]
8. Function: Append metadata (timestamp, hash)
9. Write Binary/File: Save JSON to `data/out/DATE/leads_<ts>.json`
10. Item Lists: Convert to CSV
11. Email (SMTP): Send CSV to self for review

## Environment & API Keys
- GEMINI_API_KEY: for AI analysis (optional)
- WAPPALYZER_API_KEY, WHOIS provider, etc. (future enrichment)

## Files in this folder
- `schema/lead_entity.schema.json` — Canonical lead JSON schema
- `functions/normalize.js` — Function node snippet to normalize raw inputs
- `functions/scoring.js` — Function node snippet to compute branding score
- `prompts/brand_analysis_prompt.md` — AI prompt to classify brand maturity (no outreach)

## Importing into n8n
This repo provides node code and prompts. Build the workflow in the n8n UI using the outline above and paste the Function node code from `functions/*.js`. Configure credentials for Email/HTTP and set environment variables.

## Notes
- Keep AI optional; the scoring alone is deterministic and cheap.
- Heavy scraping (JS websites) should be delegated to your existing Python scrapers and called via Webhook node.
- Persist both JSON and CSV; the JSON is the source of truth for downstream processing.