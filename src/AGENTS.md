# AGENTS.md

## Project boundary
- The DBMS app, prompts, tests, scripts, environment, users, and logs belong under this `src/` directory.
- Keep sibling analysis datasets and notebooks in the workspace root unchanged.
- Never modify the existing SQL Server schema or data.
- Treat all LLM output as untrusted; validate every generated SQL statement before execution.
- Never commit `.env`, local user data, or logs.

## Environment and commands
Use `D:\college_coding\.common_venv\Scripts\python.exe` and run commands from this directory:

```powershell
& 'D:\college_coding\.common_venv\Scripts\python.exe' -m uvicorn app.main:app --reload
& 'D:\college_coding\.common_venv\Scripts\python.exe' -m pytest -q
& 'D:\college_coding\.common_venv\Scripts\python.exe' -m pytest tests/test_validator.py -q
& 'D:\college_coding\.common_venv\Scripts\python.exe' -m pytest tests/test_auth.py -q
```

## Editing conventions
- Keep editable model prompts under `prompts/`.
- Resolve relative app-data paths under this `src/` directory.
- Log only safe metadata; never log passwords or tokens.
- Keep route protections explicit and easy to explain.
