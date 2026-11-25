# Architecture Diagram: Canva Notes

## Files

- `dbms-app-architecture.svg` — 16:9 vector visual ready to import into Canva or PowerPoint.
- `dbms-app-architecture.mmd` — editable Mermaid source for rebuilding or rearranging the flow.

## Suggested talk track

1. **Data preparation:** BTS on-time CSV files were loaded into the already-existing `AirlinesProject` SQL Server database before the web app runs. CSV ingestion is not an app endpoint.
2. **Authentication:** users register as `user`; passwords are Argon2-hashed. Login issues an HttpOnly JWT cookie with the role. FastAPI dependencies check authentication and admin privileges on protected APIs.
3. **Two query paths:** the dashboard runs fixed aggregate SELECTs. Chat and the admin console use the SQL validation path; the admin enters SQL directly, while chat first asks Gemini to propose SQL.
4. **LLM boundary:** Gemini receives the question and editable schema/business/rule prompt context, not database rows or user account records. Gemini only proposes structured SQL/refusal/explanation JSON.
5. **Guardrails:** generated chat SQL and admin SQL pass through the SQLGlot T-SQL validator before execution. It permits SELECTs against the three `dbo` tables and rejects dangerous statements and constructs. The application returns bounded rows to the interface.
6. **Results and audit:** the UI displays data as tables/charts. Only admins can inspect generated SQL; regular users see results and explanations. Authentication, query, and blocked/error events go to a rotating local log.

## Important wording

There are **not two database systems for app data**. The account store is a local JSON file containing username, password hash, and role. Flight records are in the separate SQL Server database, which has `Airline`, `Airport`, and `FlightInstance` tables.

The figure is an architecture overview, not a deployment diagram. The CSV import is a prior offline preparation step, not a live service in the request path.
