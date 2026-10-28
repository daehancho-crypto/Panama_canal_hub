# ACP Intelligence Hub — company AI integration

The public GitHub Pages frontend never accepts or stores API keys. It accepts only the base HTTPS URL of a company-approved reverse proxy, saved in browser localStorage. **Do not expose an unauthenticated public AI proxy.**

## Required endpoints

- `GET /health` → `{"status":"ok"}`
- `POST /analyze` with JSON:
  - `task`: `question` or `notice_summary`
  - `question`: user question (for `question`)
  - `document`: `{title,url,text}` (for `notice_summary`)
  - `sources`: list of `{title,url,text}`
- Response: `{"answer":"Korean grounded answer...", "citations":[{"title":"ACP document", "url":"https://pancanal.com/...pdf"}]}`

## Security prerequisites (mandatory before enabling for company use)

1. Host the proxy on an approved HTTPS environment. Store upstream API keys only in server-side secret storage, never in GitHub or JavaScript.
2. Require company identity/authentication and authorization on every request, not only CORS. The current frontend does not implement a company SSO flow; configure the proxy and its auth integration before production.
3. Restrict CORS to the exact approved GitHub Pages origin or move the frontend to an internal approved domain.
4. Enforce request size, response size, timeouts, per-user rate limits and model spending caps.
5. Validate ACP source URLs against an allowlist, verify citations and restrict model output to retrieved content. Do not assume a PDF is currently effective merely because indexed.
6. Review data classification, retention, logging, vendor training and cross-border transfer before sending voyage/charter data.
7. For automated summaries, schedule only on confirmed new or changed PDF hashes and persist results/version metadata. This is **not implemented yet**. A URL or first_seen alone does not prove a content revision.
8. Frontend indexing is partial (first 12 pages / 16k characters for a limited subset), so answers must state evidence gaps. Scanned PDF OCR, tables and revision chains require additional processing.

## Cost

The frontend and GitHub Pages have no paid AI API calls. The proxy's model may incur charges according to the company's API allocation. No scheduled AI calls are configured in this repository.
