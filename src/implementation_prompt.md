# Workspace boundary: the DBMS project lives under `src/`; treat paths below as relative to that folder. Do not modify the sibling airline-analysis datasets, notebooks, or root-level project files.

# ROLE
You are a senior engineer helping me plan a small university DBMS course project. I am the only developer and the timeline is tight, so keep everything simple and easy to explain. This is PLAN MODE: do not write implementation code yet. Produce a short, phased plan, list open questions and assumptions, and wait for my approval before building.

# PROJECT SUMMARY
A secure web app on top of an EXISTING SQL Server database of US domestic flights (BTS on-time data). The app has:
1. Registration, login and role-based access (FastAPI backend, plain HTML/CSS/JS frontend)
2. A text-to-SQL chatbot powered by the Gemini Flash API, wrapped in strong security layers
3. An admin-only read-only SQL console
4. Logging to a file

The main learning goals are database security (injection defence, least privilege in the app, logging) and clean API design. I'll present it and justify each choice, so simple and explainable beats heavy and complete.

# EXISTING DATABASE (already built and loaded; do NOT modify, redesign or add anything to it)
Server: local SQL Server, database `AirlinesProject`, accessed from Python via pyodbc. About 3.4M rows in FlightInstance (11 busiest US origin airports, 7 major airlines, 2 years).

```sql
CREATE TABLE dbo.Airline (
    carrier_code VARCHAR(5) NOT NULL,
    airline_name VARCHAR(100) NULL,
    CONSTRAINT PK_Airline PRIMARY KEY (carrier_code)
);

CREATE TABLE dbo.Airport (
    airport_code CHAR(3) NOT NULL,
    airport_name VARCHAR(150) NULL,
    city VARCHAR(100) NULL,
    state VARCHAR(50) NULL,
    CONSTRAINT PK_Airport PRIMARY KEY (airport_code)
);

CREATE TABLE dbo.FlightInstance (
    carrier_code VARCHAR(5) NOT NULL,
    flight_date DATE NOT NULL,
    flight_number VARCHAR(10) NOT NULL,
    tail_number VARCHAR(10) NULL,
    origin_airport_code CHAR(3) NOT NULL,
    destination_airport_code CHAR(3) NOT NULL,
    scheduled_departure_time TIME(0) NULL,
    actual_departure_time TIME(0) NULL,
    scheduled_elapsed_minutes INT NULL,
    actual_elapsed_minutes INT NULL,
    departure_delay_minutes INT NULL,
    arrival_delay_minutes INT NULL,
    wheels_off_time TIME(0) NULL,
    taxi_out_minutes INT NULL,
    CONSTRAINT PK_FlightInstance PRIMARY KEY CLUSTERED
        (carrier_code, flight_date, flight_number, origin_airport_code),
    CONSTRAINT FK_FlightInstance_Airline FOREIGN KEY (carrier_code) REFERENCES dbo.Airline(carrier_code),
    CONSTRAINT FK_FlightInstance_OriginAirport FOREIGN KEY (origin_airport_code) REFERENCES dbo.Airport(airport_code),
    CONSTRAINT FK_FlightInstance_DestinationAirport FOREIGN KEY (destination_airport_code) REFERENCES dbo.Airport(airport_code)
);
```
Data notes the chatbot's business context must reflect: origins are only the 11 busiest airports, but destinations can be any airport in the Airport table; there are no cancellation or diversion fields and no arrival-time columns (only arrival delay); delay columns can be negative (early) or NULL.

# HARD CONSTRAINTS
- Do NOT create any new database objects: no tables, schemas, views, logins or users. The app runs only SELECT queries directly against the existing `dbo` tables, using a connection configured through environment variables (never `sa` in code or committed files).
- Because there is no DB-level restriction, the SQL validator is the main line of defence, so make it strong.
- Everything runs locally. No cloud deployment.

# WHAT TO BUILD (MVP)

## Auth and RBAC (no database table)
- Registration and login with argon2 or bcrypt hashing, a basic password policy, short-lived JWTs
- Store users in a simple local file (e.g. a JSON file, or SQLite if you think it's better; propose one and justify it), not in SQL Server. Handle concurrent writes safely.
- Basic brute-force protection (e.g. in-memory failed-login counter with temporary lockout)
- Roles: `user` (chat only) and `admin` (chat + SQL console + log viewer), enforced by API dependencies on every protected endpoint
- Public registration only creates `user`. Propose a simple way to create the first admin (e.g. a CLI script or env variable).

## Text-to-SQL chatbot (the core)
- Gemini Flash API with structured JSON output: `{ "sql": ..., "refusal_reason": ..., "explanation": ... }`
- Prompt assembled from separate EDITABLE files, not hardcoded in Python: schema metadata, business context and column descriptions, few-shot examples, and strict rules. I will tune these myself later.
- The LLM sees only schema metadata, never raw data or user info. Its output is treated as untrusted.
- Pre-LLM input checks plus explicit handling of prompt injection, jailbreaks, out-of-scope requests (e.g. "show the users", "ignore previous instructions", "drop the table"), unanswerable questions and ambiguous questions, each returning a clear, safe refusal
- Validation before execution (sqlglot, T-SQL dialect, AST-based, not regex): exactly one statement, SELECT only, allowlist of the three `dbo` tables, block sys.*, INFORMATION_SCHEMA, xp_/sp_ procedures, SELECT INTO, OPENROWSET/OPENQUERY, comments, dynamic SQL and multi-statement batches
- Force a TOP/row cap, query timeout and result-size limit
- One retry: if execution fails, feed the error back to the model once, then fail gracefully
- Response: columns, rows, the generated SQL (for transparency) and the explanation
- Structure the pipeline as one function (question in, result/refusal out) so I can run a list of questions through it later

## Admin SQL console
- Same validator (single SELECT only), with row and time limits. Admin-only.

## Logging
- Python `logging` to a rotating `.log` file (no DB table)
- Log: timestamp, username, role, client IP, event type (register / login success / login failure / chat / admin query / blocked), question, generated SQL, validator verdict and reason, row count, latency
- Never log passwords or tokens
- Optional and small: an admin-only page showing the last N log lines

## Frontend (plain HTML/CSS/JS, served by FastAPI)
- Pages: register, login, chat, admin SQL console (plus the optional log view)
- Chat shows the result table, the generated SQL, and clear refusal messages
- Auto-chart of results with Chart.js (bar/line chosen from the result shape, e.g. category + number -> bar, date + number -> line)
- Briefly recommend where to store the JWT (httpOnly cookie vs memory) and set sensible CORS and security headers. Keep it simple.

# OUT OF SCOPE (do not plan or build)
- Any new SQL Server objects, DB design, ingestion, query optimization, relational algebra
- Gold-set evaluation harness, adversarial test suite, k-means or analytics pages
- Cloud deployment, Docker, CI

# WHAT I WANT FROM YOU NOW
1. Ask at most 5 important clarifying questions first.
2. Then propose:
   - A small folder structure
   - A plan in at most 4 phases (suggested: 1 backend skeleton + DB connection + logging; 2 auth/RBAC; 3 validator + Gemini pipeline; 4 frontend + charts + README with threat model and demo script), each with tasks, acceptance criteria and how to verify
   - API endpoint list with auth requirements
   - A short threat model table (threat, mitigating layer)
   - Dependency list (minimal; justify each)
   - Key risks and decisions I need to make
3. Propose a short AGENTS.md (or CLAUDE.md) with conventions and run/test commands.
4. Do NOT write implementation code until I approve the plan.

# WORKING STYLE
- Small, reviewable steps; each phase ends with something runnable
- A few focused pytest tests, especially for the validator and auth
- Do not add dependencies without asking
- Briefly explain each design choice in terms of the DBMS/security concept it demonstrates