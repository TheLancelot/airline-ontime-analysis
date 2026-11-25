# Airline On-Time DBMS Security Demo

The DBMS project is isolated in this `src` folder. The sibling analysis data and notebooks remain in the workspace root. The existing SQL Server database is read-only from this app; the app does not create or alter database objects.

## Project layout

- `app/` — FastAPI API, authentication, validator, templates, and static assets
- `prompts/` — editable Gemini schema, business-context, examples, and rules
- `tests/` — focused API, auth, database, and validator tests
- `scripts/` — local admin bootstrap utility
- `data/users.json` — local account store
- `logs/app.log` — rotating application log
- `.env` — local settings and secrets; never commit this file

## Run locally on Windows

Open PowerShell and run:

```powershell
Set-Location 'D:\college_coding\airline_ontime_analysis\src'
```

The DBMS environment file and account store were moved into this folder. Keep the existing `.env`; do not overwrite it with `.env.example`. For a fresh clone only, copy `.env.example` to `.env`, then set a private `JWT_SECRET_KEY` and `GEMINI_API_KEY`.

The SQL Server defaults use Windows integrated authentication for `DESKTOP-LVP84RD\MSSQLSERVER01` and `AirlinesProject`. No SQL username or password is required. `USER_STORE_PATH` and `LOG_FILE_PATH` relative values are resolved under this `src` folder, regardless of the shell's working directory.

Use the shared virtual environment:

```powershell
& 'D:\college_coding\.common_venv\Scripts\python.exe' -m pip install -r requirements.txt
& 'D:\college_coding\.common_venv\Scripts\python.exe' -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`. The landing page links to registration, login, and the admin sign-in flow. Registration leads to login; after login, regular users go to the dashboard and admins go to the SQL console. Authenticated pages greet the signed-in user and provide a logout action.

## Create an admin account

Run this from any folder in PowerShell; the script locates the DBMS project and its `src\.env` automatically:

```powershell
& 'D:\college_coding\.common_venv\Scripts\python.exe' 'D:\college_coding\airline_ontime_analysis\src\scripts\create_admin.py' admin_name
```

You can omit `admin_name` to be prompted for it. The script securely prompts for the password twice; passwords are not command-line arguments. Passwords must be at least 8 characters and contain uppercase, lowercase, and a number.

If that username already has a regular account, the script will ask for that account's current password before promoting it to admin. If it is already an admin, no change is made. After creation or promotion, log in through the app; admin accounts are routed to the SQL console.

## Tests

Run from this folder:

```powershell
& 'D:\college_coding\.common_venv\Scripts\python.exe' -m pytest -q
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
