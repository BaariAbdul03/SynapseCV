**SynapseCV Product Hardening And Daily-Use Upgrade Plan**

**Summary**
SynapseCV is a Flask resume intelligence app with a recruiter workspace, PDF parsing, Groq/Gemini AI analysis, role templates, archives, API keys, and export tools. Current tests pass (`12 passed`), Ruff passes, and route smoke checks return 200, but the product has security, reliability, UX, and maintainability gaps that should be addressed before treating it as business-critical daily software.

**Top Findings To Fix**
- Critical security: AI/user-controlled fields are rendered with `innerHTML` in the workspace and leaderboard, creating XSS risk from resume text, archive data, and model output. Main area: [static/script.js](D:\ResumeParser\SynapseCV\static\script.js:606).
- Missing CSRF protection on login/register, sandbox OAuth, role template saves, API key creation/deletion, and archive deletion. Session-cookie auth plus POST/DELETE endpoints need CSRF tokens.
- Production can boot with the default `SECRET_KEY`; fail startup in production when required secrets are missing. See [app/config.py](D:\ResumeParser\SynapseCV\app\config.py:5).
- Product behavior drift: UI requires a non-empty job description, while backend/README support “infer from resume” mode. See [static/script.js](D:\ResumeParser\SynapseCV\static\script.js:472).
- AI stack drift: the app uses `AIService` Groq-first fallback, but tests still target the older standalone Gemini service. Config/docs also disagree on primary provider and model versions.
- No server-side schema validation of AI output: score range, required fields, URL safety, list types, and “reasoning final score equals match_percentage” are prompt-only rules.
- Synchronous batch parsing can tie up web requests with multiple AI calls. This risks timeouts and poor UX for daily bulk use.
- Encoding/mojibake appears across README/templates/CSS/JS (`â€”`, `ðŸ`, `â˜…`), which will visibly degrade brand polish.
- Workspace UX is dense and visually strong, but lacks daily recruiter essentials: archive search/filter/sort, candidate comparison, shortlist statuses, notes, score explanations users can trust, and per-file batch progress.
- Tests are too narrow: no tests for current AI facade, parse persistence, auth flows, CSRF/security headers in production config, frontend XSS safety, archive ownership, or batch ranking behavior.

**Phase 1: Stabilize And Secure**
- Replace unsafe `innerHTML` rendering of dynamic candidate/model data with DOM construction plus `textContent`; whitelist and validate GitHub/LinkedIn URLs before making anchors.
- Add CSRF protection to all browser session POST/DELETE flows; keep public REST API key endpoints CSRF-exempt only where appropriate.
- Enforce production config validation for `SECRET_KEY`, database URL, OAuth secrets if OAuth is required, and at least one AI provider key.
- Add server-side AI response normalization with a strict schema: strings, arrays, integer score 0-100, safe URLs, default values, and scoring mismatch detection.
- Fix encoding across docs/templates/static assets and ensure files are saved as UTF-8.
- Add tests for XSS escaping, CSRF enforcement, production secret failure, AI schema validation, and archive ownership.

**Phase 2: Make Parsing Reliable**
- Consolidate AI code into one tested facade; remove or clearly deprecate the older Gemini service.
- Align README, config, prompts, and tests with the actual provider order: Groq primary, Gemini fallback, configurable model names.
- Move batch parsing to a background job model with job IDs, status polling, per-file progress, cancellation, and retry-safe persistence.
- Store parse metadata: filename, provider used, model used, latency, error reason, extracted text length, page count, and created-by user/API key.
- Add per-file size validation and clarify batch upload limits; avoid a misleading 10-file promise if total Flask upload limit is 5MB.
- Add integration tests for single parse, batch parse, failed PDF, AI failure fallback, and save-to-archive behavior using mocked AI.

**Phase 3: Daily Recruiter Workflow**
- Upgrade archives into a usable candidate workspace: search, sort by score/date/role, filter by role/status, delete/restore, and open detail view.
- Add candidate statuses: New, Reviewed, Shortlisted, Rejected, Interviewing, Hired, with notes and last-updated timestamps.
- Add comparison mode for 2-5 candidates against the same JD, highlighting strengths, gaps, and deciding factors.
- Make inferred-role mode first-class: allow scanning without JD, show “Inferred role” clearly, and let users convert it into a saved role template.
- Replace `prompt()` for template naming with an in-app modal and validation.
- Improve export usefulness: CSV includes status/notes/provider/date; PDF report has clean branding, no mojibake, and audit-friendly scoring details.

**Phase 4: Business-Grade Platform**
- Add organization/team model, recruiter roles, shared templates, and shared candidate archives.
- Add API key metadata: last used, created by, scopes, optional expiry, revoke reason, and per-key rate limits.
- Add audit logging for parse, export, archive delete, API key create/revoke, and template changes.
- Add observability: structured parse metrics, provider failure rates, average latency, queue depth, and daily usage counts.
- Add retention controls for GDPR/business policy: archive retention, delete candidate permanently, and export candidate data.
- Add deployment discipline: Alembic migrations instead of `create_all()` plus ad hoc DDL, production smoke tests, and CI running pytest + Ruff.

**Assumptions**
- Primary daily users are recruiters/HR teams scanning PDFs against job descriptions.
- Anonymous sandbox scanning can remain for demos, but production business workflows should require login unless explicitly configured otherwise.
- Existing visual style can remain, but UX should become more task-oriented and less fragile before adding new features.
