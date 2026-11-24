from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import get_current_user
from app.config import settings
from app.db.connection import get_sql_server_connection
from app.logging_conf import get_logger
from app.security.validator import validate_select_sql

router = APIRouter(prefix="/api/admin", tags=["admin"])
logger = get_logger("admin")


@router.post("/query")
async def admin_query(payload: dict, request: Request, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    sql = str(payload.get("sql", "")).strip()
    if not sql:
        raise HTTPException(status_code=400, detail="SQL is required")

    validation = validate_select_sql(sql)
    if not validation.is_valid:
        logger.warning("admin_blocked | username=%s | reason=%s", current_user["username"], validation.reason)
        return {"status": "refused", "reason": validation.reason, "columns": [], "rows": []}

    try:
        conn = get_sql_server_connection()
        if conn is None:
            return {
                "status": "demo",
                "reason": "Demo mode only: no live SQL Server configured.",
                "columns": ["airport_code", "airport_name"],
                "rows": [["ATL", "Hartsfield-Jackson Atlanta International Airport"]],
            }
        try:
            cursor = conn.cursor()
            cursor.execute(validation.normalized_sql)
            columns = [col[0] for col in cursor.description] if cursor.description else []
            rows = [list(row) for row in cursor.fetchmany(50)]
        finally:
            conn.close()
        logger.info("admin_query | username=%s | sql=%s | rows=%s", current_user["username"], validation.normalized_sql, len(rows))
        return {"status": "ok", "reason": "Query executed", "columns": columns, "rows": rows}
    except Exception as exc:
        logger.exception("admin_query_error | username=%s", current_user["username"])
        return {
            "status": "error",
            "reason": "The query could not be completed. Check the database connection and try again.",
            "columns": [],
            "rows": [],
        }


@router.get("/logs")
async def admin_logs(request: Request, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    log_path = settings.LOG_FILE_PATH
    if not log_path.exists():
        return {"lines": []}
    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-settings.MAX_LOG_LINES:]
    logger.info("admin_logs_requested | username=%s | count=%s", current_user["username"], len(lines))
    return {"lines": lines}
