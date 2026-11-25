from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import get_current_user
from app.db.connection import get_sql_server_connection
from app.logging_conf import get_logger
from app.security.validator import validate_select_sql
from app.services.gemini_client import GeminiClient, GeminiServiceError
from app.config import settings

router = APIRouter(prefix="/api", tags=["chat"])
logger = get_logger("chat")


@router.post("/chat")
async def chat_endpoint(payload: dict, request: Request, current_user: dict = Depends(get_current_user)):
    question = str(payload.get("question", "")).strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    client = GeminiClient(api_key=settings.GEMINI_API_KEY)

    try:
        model_response = client.generate_sql(question)
    except GeminiServiceError as exc:
        logger.error(
            "chat_model_error | username=%s | question=%s | error=%s",
            current_user["username"],
            question,
            exc,
        )
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    sql = str(model_response.get("sql", "")).strip()
    refusal = model_response.get("refusal_reason")
    explanation = model_response.get("explanation", "")

    if refusal or not sql:
        logger.info(
            "chat_blocked | username=%s | role=%s | question=%s | reason=%s",
            current_user["username"],
            current_user["role"],
            question,
            refusal,
        )
        return {
            "status": "refused",
            "refusal_reason": refusal,
            "explanation": explanation,
            "columns": [],
            "rows": [],
        }

    validation = validate_select_sql(sql)
    if not validation.is_valid:
        logger.warning(
            "chat_validation_failed | username=%s | question=%s | reason=%s",
            current_user["username"],
            question,
            validation.reason,
        )
        return {
            "status": "refused",
            "refusal_reason": validation.reason,
            "explanation": explanation,
            "columns": [],
            "rows": [],
        }

    try:
        conn = get_sql_server_connection()
        if conn is None:
            return {
                "status": "demo",
                "refusal_reason": None,
                "explanation": "The app is running in offline demo mode because SQL Server is not configured.",
                "columns": ["airport_code", "airport_name"],
                "rows": [["ATL", "Hartsfield-Jackson Atlanta International Airport"]],
                **(
                    {"sql": validation.normalized_sql}
                    if current_user["role"] == "admin"
                    else {}
                ),
            }

        safe_sql = validation.normalized_sql
        try:
            cursor = conn.cursor()
            cursor.execute(safe_sql)
            columns = [col[0] for col in cursor.description] if cursor.description else []
            rows = [list(row) for row in cursor.fetchmany(50)]
        finally:
            conn.close()
        logger.info(
            "chat_success | username=%s | role=%s | sql=%s | rows=%s",
            current_user["username"],
            current_user["role"],
            safe_sql,
            len(rows),
        )
        result = {
            "status": "ok",
            "refusal_reason": None,
            "explanation": explanation,
            "columns": columns,
            "rows": rows,
        }
        if current_user["role"] == "admin":
            result["sql"] = safe_sql
        return result
    except Exception as exc:
        logger.exception("chat_exception | username=%s | question=%s", current_user["username"], question)
        return {
            "status": "error",
            "refusal_reason": "The query could not be completed. Check the database connection and try again.",
            "explanation": "The query could not be completed.",
            "columns": [],
            "rows": [],
        }
