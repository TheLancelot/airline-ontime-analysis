# DBMS Course Project Plan

## Problem and approach
This project is a small, explainable DBMS security app built on the existing local SQL Server database `AirlinesProject`. The core design is to keep the database untouched, enforce every query through a strong validator, and separate concerns cleanly: FastAPI backend, file-backed auth, Gemini-based text-to-SQL with refusal rules, admin-only console, and rotating-file logging. The plan keeps each phase runnable and reviewable, with a small set of focused tests for validation and auth.

## Assumptions and open questions
- Assumption: the app will use a single local FastAPI service with plain HTML/CSS/JS templates and static assets. No cloud or Docker.
- Assumption: user credentials will be stored in a local JSON file for simplicity and easy audit; if concurrent writes become a concern, we can gate with a lock or SQLite file-backed store.
- Assumption: the first admin can be created via a short CLI bootstrap script or an environment variable in a local `.env` file, not via a database user.
- Open question: do we want JWTs in an `HttpOnly` cookie or in the browser memory with a simple bearer flow? Recommended default is cookie for a local demo with lower accidental leakage risk.
- Open question: should we expose a minimal admin log viewer page or only a file download/log summary? The plan includes optional page viewing as a small enhancement.

## Proposed folder structure
The project files and runtime state are now isolated under `airline_ontime_analysis/src/`.

```text
airline_ontime_analysis/src/
├── app/
│   ├── api/
│   │   ├── deps.py
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   └── admin.py
│   │   └── schemas.py
│   ├── auth/
│   │   ├── models.py
│   │   ├── service.py
│   │   └── storage.py
│   ├── config.py
│   ├── db/
│   │   ├── connection.py
│   │   └── queries.py
│   ├── logging_conf.py
│   ├── security/
│   │   ├── validator.py
│   │   ├── prompt_rules.py
│   │   └── executor.py
│   ├── services/
│   │   ├── gemini_client.py
│   │   └── chat_pipeline.py
│   ├── templates/
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── chat.html
│   │   └── admin.html
│   ├── static/
│   │   ├── styles.css
│   │   └── app.js
│   └── main.py
├── tests/
│   ├── test_auth.py
│   ├── test_validator.py
│   └── test_chat_pipeline.py
├── prompts/
│   ├── schema_metadata.md
│   ├── business_context.md
│   ├── few_shots.md
│   └── rules.md
├── .env.example
├── requirements.txt
├── README.md
├── AGENTS.md
└── scripts/
    └── create_admin.py
```

## Phase plan
### Phase 1 — Backend skeleton, DB connectivity, logging
Tasks:
- Create FastAPI app skeleton and environment config.
- Add SQL Server connection helper using `pyodbc` and env-based credentials.
- Add rotating file logger with structured metadata fields and redaction rules.
- Create basic health and app startup wiring.
Acceptance criteria:
- App starts locally.
- `pyodbc` connection can be opened to `AirlinesProject` using environment variables only.
- Log file rotates correctly and records key events without storing passwords or tokens.
How to verify:
- Run a startup smoke test and a direct DB connectivity probe.
- Check log file output for timestamp, username, role, event type, and safe metadata.

### Phase 2 — Auth and RBAC
Tasks:
- Implement local user store (JSON file or SQLite; recommend JSON for simplicity, or SQLite if concurrent-safe file locking becomes necessary).
- Add password hashing with `argon2` or `bcrypt`, password policy, and failed-login lockout.
- Add JWT creation/verification, role checks, and protected-route dependencies.
- Add first-admin bootstrap via CLI or env flag.
Acceptance criteria:
- A user can register, log in, and receive a valid token.
- Only `user` may access chat; only `admin` may access SQL console and log view.
- Failed login attempts trigger lockout and are logged without leaking credentials.
How to verify:
- Run focused auth tests for registration, invalid login, and RBAC enforcement.
- Inspect responses for 401/403 behavior.

### Phase 3 — SQL validator and Gemini pipeline
Tasks:
- Build AST-based validator using `sqlglot` (T-SQL dialect) and whitelist enforcement for `dbo.Airline`, `dbo.Airport`, `dbo.FlightInstance` only.
- Reject comments, multi-statements, `SELECT INTO`, `OPENROWSET`, `OPENQUERY`, `sys.*`, `INFORMATION_SCHEMA`, `xp_`/`sp_` calls, dynamic SQL, and anything outside exact read-only patterns.
- Add row/time/result caps, single-statement enforcement, and safe execution wrapper.
- Add text-to-SQL prompt assembly from editable prompt files, refusal logic, and one-level retry loop on SQL errors.
Acceptance criteria:
- The validator blocks unsafe queries and allows a narrow set of safe read-only selects.
- The pipeline returns either result rows or a structured refusal with a clear explanation.
- Query execution respects TOP/row caps and fails gracefully with a safe message.
How to verify:
- Run focused pytest tests covering safe/unsafe SQL cases and refusal handling.
- Run a small list of known-good questions through the pipeline without exposing raw data to the model.

### Phase 4 — Frontend, charts, docs, and demo readiness
Tasks:
- Build plain HTML/CSS/JS pages for register, login, chat, and admin console.
- Add Chart.js output for category/number and date/number charts based on result shape.
- Add optional admin log viewer page and README with threat model, edge-case notes, and demo script.
- Add final smoke tests and a concise AGENTS.md/CLAUDE.md convention file.
Acceptance criteria:
- Users can register/login and submit a chat prompt.
- Admin can run safe SQL queries only and view log summaries.
- README clearly explains security choices and demo steps.
How to verify:
- Run a short manual demo script using a few safe questions and one blocked query.
- Confirm headers, cookie policy, and CORS settings are sensible for local use.

## API endpoint list
Public:
- `POST /api/register` – create a user with role `user`
- `POST /api/login` – authenticate and issue a JWT
- `GET /api/health` – startup/DB connectivity check

Authenticated user:
- `POST /api/chat` – submit a natural-language question, return result or refusal
- `GET /api/chat/history` – optional recent user prompts (if desired, keep minimal)

Admin only:
- `POST /api/admin/query` – run safe read-only SQL through the same validator
- `GET /api/admin/logs` – last N log lines or summary to view log activity

Note: if we keep the UI simple, all routes can serve the templates and small static assets directly under the same app.

## Threat model table
| Threat | Mitigating layer |
|---|---|
| SQL injection via user prompt or admin console | AST-based validator, single SELECT-only enforcement, allowlist of tables, comment/dynamic SQL rejection |
| Prompt injection or jailbreak in chatbot | strict system prompt, refusal rules, no raw data exposure, context-only schema metadata |
| Accidental privilege escalation | JWT verification, route-level RBAC checks, admin-only endpoints |
| Credential leakage | hash passwords with bcrypt/argon2, never log secrets, use HttpOnly cookies |
| Brute-force login attacks | failed-login counter + temporary lockout |
| Unsafe data exfiltration or large queries | TOP cap, row cap, time limit, result-size cap |
| Server-side log leakage | rotating file logs, no tokens/passwords, admin-only log viewer |

## Minimal dependency list
- `fastapi` – simple API server and template serving
- `uvicorn` – local app runner
- `pyodbc` – direct SQL Server connectivity
- `python-dotenv` – environment variable loading
- `argon2-cffi` or `bcrypt` – password hashing
- `PyJWT` – short-lived JWT issuance and validation
- `sqlglot` – SQL AST parsing and validation for T-SQL
- `google-generativeai` or SDK for Gemini Flash – text-to-SQL backend
- `python-dotenv` and config helpers – keep local secret management simple
- `pytest` – early validation of auth and validator behavior
- `chart.js` – frontend chart rendering (CDN-based, no npm build needed)
- `jinja2` – if templates are rendered server-side

Justification: each package is directly tied to a security or course-learning outcome; no heavy framework or production stack is introduced.

## Key risks and decisions
- Risk: the SQL validator must be strong enough to override any DB-level security gaps; this is the course’s main teaching point.
- Decision: do not create any new database objects or broad application features. Keep the DB read-only and the app focused.
- Risk: Gemini may return unsafe SQL or unhelpful answers; the project needs a structured JSON schema and refusal logic before execution.
- Decision: one retry is enough for a small demo; do not do recursive recovery or fuzzy prompt hacking beyond the basic safeguard.
- Risk: file-backed auth can become a concurrency issue; use a lock or SQLite if needed, but keep the first version simple.
- Decision: keep the app local-only and explainable; that makes the security story easier to present in a short university demo.

## Recommended AGENTS.md
```md
# AGENTS.md

## Project conventions
- Keep the app local-only and explainable; do not add cloud or deployment tooling.
- Never modify the existing SQL Server schema or data.
- Treat all LLM output as untrusted; run every generated SQL through the validator before execution.
- Prefer small, reviewable changes and focused pytest tests.
- Never commit secrets; use `.env` locally and keep credentials out of version control.

## Commands
- Run app: `uvicorn app.main:app --reload`
- Run tests: `pytest -q`
- Run a single validator test: `pytest tests/test_validator.py -q`
- Run a single auth test: `pytest tests/test_auth.py -q`

## When editing
- Keep prompt templates and rules in editable files under `prompts/`.
- Log only safe metadata; never include passwords or tokens.
- Keep route protections explicit and easy to explain in the classroom.
```

## Verification checklist for each phase
- Phase 1: app boots and DB connectivity works
- Phase 2: register/login and RBAC enforcement pass tests
- Phase 3: validator blocks unsafe SQL and safe queries execute
- Phase 4: demo flow and README are clear enough for a short live presentation

This plan stays intentionally simple and easy to defend in a DBMS/security presentation, without adding unnecessary production complexity.
