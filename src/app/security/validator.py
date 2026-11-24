from __future__ import annotations

import re
from dataclasses import dataclass, field

from sqlglot import parse_one
from sqlglot import exp

from app.config import settings


@dataclass
class ValidationResult:
    is_valid: bool
    reason: str = ""
    normalized_sql: str = ""
    tables: list[str] = field(default_factory=list)


def _extract_table_names(expression: exp.Expression) -> list[str]:
    tables: list[str] = []
    for table in expression.find_all(exp.Table):
        table_name = (table.name or "").strip()
        db_name = (table.db or "").strip()
        if table_name:
            qualifier = f"{db_name}.{table_name}" if db_name else table_name
            tables.append(qualifier.lower())
    return tables


def validate_select_sql(sql: str, max_rows: int = settings.MAX_ROWS) -> ValidationResult:
    if sql is None or not str(sql).strip():
        return ValidationResult(False, "SQL query is empty.")

    text = str(sql).strip()
    if text.endswith(";"):
        text = text[:-1].strip()

    if "--" in text or "/*" in text or "*/" in text:
        return ValidationResult(False, "Comments are not allowed.")

    if re.search(r"(?is)\b(INSERT|UPDATE|DELETE|ALTER|DROP|CREATE|TRUNCATE|MERGE|GRANT|REVOKE|EXEC|EXECUTE|OPENROWSET|OPENQUERY|SELECT\s+INTO)\b", text):
        return ValidationResult(False, "Only read-only SELECT statements are allowed.")

    if re.search(r"(?is)(?:\bsp_|\bxp_)\w+|\b(?:sys|information_schema)\b|\@\w+|(?<![A-Za-z0-9_])\?", text):
        return ValidationResult(False, "System objects, stored procedures, and dynamic SQL are blocked.")

    if ";" in text:
        return ValidationResult(False, "Only a single SQL statement is permitted.")

    try:
        parsed = parse_one(text, read="tsql")
    except Exception as exc:  # pragma: no cover - parser failure
        return ValidationResult(False, f"SQL could not be parsed: {exc}")

    if not isinstance(parsed, exp.Select):
        return ValidationResult(False, "Only SELECT statements are allowed.")

    if isinstance(parsed, exp.Subquery):
        return ValidationResult(False, "Nested subqueries are not allowed.")

    tables = _extract_table_names(parsed)
    if not tables:
        return ValidationResult(False, "No valid table references found.")

    allowed = {item.lower() for item in ["dbo.airline", "airline", "dbo.airport", "airport", "dbo.flightinstance", "flightinstance"]}
    for table in tables:
        if table not in allowed:
            return ValidationResult(False, f"Table is not allowed: {table}")

    normalized_sql = enforce_top_limit(text, max_rows)
    return ValidationResult(True, "Validated.", normalized_sql, tables)


def enforce_top_limit(sql: str, max_rows: int) -> str:
    text = sql.strip()
    if re.search(r"(?is)^\s*select\s+top\b", text):
        return text
    if re.search(r"(?is)^\s*select\b", text):
        return re.sub(r"(?is)^\s*select\b", f"SELECT TOP {max_rows}", text, count=1)
    return text
