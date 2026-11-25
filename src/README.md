# Airline On-Time Database system and app

The DBMS project is isolated in this `src` folder. The sibling analysis data and notebooks remain in the workspace root. The existing SQL Server database is read-only from this app; the app does not create or alter database objects.

## Project layout

- `app/` — FastAPI API, authentication, validator, templates, and static assets
- `prompts/` — editable Gemini schema, business-context, examples, and rules
- `tests/` — focused API, auth, database, and validator tests
- `scripts/` — local admin bootstrap utility
- `data/users.json` — local account store
- `logs/app.log` — rotating application log
- `.env` — local settings and secrets; never commit this file

## Clone and run locally on Windows

In PowerShell, clone the repository into a folder of your choice. Replace `<repository-url>` with the repository's clone URL:

```powershell
git clone <repository-url> airline-ontime-analysis
Set-Location .\airline-ontime-analysis\src
```

If you chose a different clone folder name or location, change the `Set-Location` path to that clone's `src` folder. The commands below use paths relative to `src`, so they do not depend on where you cloned the repository.

Create a local environment file for this clone if one does not already exist. Do not overwrite an existing `.env`:

```powershell
if (-not (Test-Path .\.env)) { Copy-Item .\.env.example .\.env }
notepad .\.env
```

In `.env`, set `JWT_SECRET_KEY`, your Gemini API key if you want live Gemini responses, and the SQL Server instance/database names available on your machine. The example SQL Server instance is specific to the original development machine. The app uses Windows integrated authentication; your Windows account must have read access to the configured database. Install Microsoft ODBC Driver 18 for SQL Server if it is not already installed. No SQL username or password is configured by the app.

Create a virtual environment inside the cloned project and install its requirements:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Start the app from the `src` folder:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`. The landing page links to registration, login, and the admin sign-in flow. Registration leads to login; after login, regular users go to the dashboard and admins go to the SQL console. Authenticated pages greet the signed-in user and provide a logout action.

The dashboard serves exact values precomputed from the current static `AirlinesProject` data, so loading the dashboard does not scan the 3.4M-row flight table. If the SQL Server dataset changes, update the snapshot constants in `app/api/routes/dashboard.py`.

## Create an admin account

With PowerShell in the cloned project's `src` folder, run:

```powershell
.\.venv\Scripts\python.exe .\scripts\create_admin.py admin_name
```

You can omit `admin_name` to be prompted for it. The script securely prompts for the password twice; passwords are not command-line arguments. Passwords must be at least 8 characters and contain uppercase, lowercase, and a number.

If that username already has a regular account, the script will ask for that account's current password before promoting it to admin. If it is already an admin, no change is made. After creation or promotion, log in through the app; admin accounts are routed to the SQL console.

## Run tests

Run from the cloned project's `src` folder:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Demo outline

1. Register a regular user and log in to view the dashboard.
2. Ask a read-only question in chat; admins can inspect the validated SQL.
3. Use an admin account to open the SQL console and review recent logs.
4. Try a blocked statement such as `DROP TABLE dbo.Airline` and confirm it is refused.

## Security overview

- SQL Server access uses Windows integrated authentication and existing tables only.
- Generated SQL is treated as untrusted and must pass AST validation before execution.
- Passwords are Argon2-hashed; JWTs are set in an `HttpOnly` cookie.
- Admin routes enforce role checks server-side.
- Logs rotate locally and must not contain passwords or tokens.
