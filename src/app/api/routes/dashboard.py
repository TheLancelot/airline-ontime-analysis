from __future__ import annotations

from copy import deepcopy
from threading import Lock
from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException, Response

from app.api.deps import get_current_user
from app.config import settings
from app.db.connection import get_sql_server_connection
from app.logging_conf import get_logger

router = APIRouter(prefix="/api", tags=["dashboard"])
logger = get_logger("dashboard")
_dashboard_cache: dict | None = None
_dashboard_cache_expires_at = 0.0
_dashboard_cache_lock = Lock()


@router.get("/dashboard")
async def dashboard_data(
    response: Response,
    current_user: dict = Depends(get_current_user),
):
    global _dashboard_cache, _dashboard_cache_expires_at

    now = perf_counter()
    with _dashboard_cache_lock:
        if _dashboard_cache is not None and now < _dashboard_cache_expires_at:
            response.headers["X-Dashboard-Cache"] = "HIT"
            logger.info("dashboard_cache_hit | username=%s", current_user["username"])
            return deepcopy(_dashboard_cache)

    connection = None
    stage = "connection"
    stage_started = perf_counter()
    try:
        print(
            f"Dashboard: connecting to SQL Server for {current_user['username']}",
            flush=True,
        )
        connection = get_sql_server_connection()
        connection.timeout = settings.MAX_QUERY_SECONDS
        cursor = connection.cursor()
        elapsed = perf_counter() - stage_started
        logger.info(
            "dashboard_connection_ready | username=%s | timeout_seconds=%s | "
            "elapsed_seconds=%.3f",
            current_user["username"],
            connection.timeout,
            elapsed,
        )
        print(
            f"Dashboard: connected in {elapsed:.2f}s; "
            f"query timeout={connection.timeout}s",
            flush=True,
        )

        stage = "metrics_query"
        stage_started = perf_counter()
        logger.info(
            "dashboard_metrics_query_start | username=%s | timeout_seconds=%s",
            current_user["username"],
            connection.timeout,
        )
        print("Dashboard: starting metrics query", flush=True)
        cursor.execute(
            """
            SELECT
                COUNT_BIG(*) AS total_flights,
                (SELECT COUNT_BIG(*) FROM dbo.Airline) AS total_carriers,
                (SELECT COUNT_BIG(*) FROM dbo.Airport) AS total_airports,
                AVG(CAST(arrival_delay_minutes AS FLOAT)) AS average_arrival_delay,
                AVG(CAST(departure_delay_minutes AS FLOAT)) AS average_departure_delay,
                AVG(
                    CASE
                        WHEN arrival_delay_minutes IS NOT NULL
                        THEN CASE WHEN arrival_delay_minutes <= 15 THEN 1.0 ELSE 0.0 END
                    END
                ) * 100.0 AS on_time_arrival_percentage
            FROM dbo.FlightInstance
            """
        )
        metrics = cursor.fetchone()

        elapsed = perf_counter() - stage_started
        logger.info(
            "dashboard_metrics_query_complete | username=%s | elapsed_seconds=%.3f",
            current_user["username"],
            elapsed,
        )
        print(f"Dashboard: metrics query completed in {elapsed:.2f}s", flush=True)

        stage = "carrier_delay_query"
        stage_started = perf_counter()
        logger.info(
            "dashboard_carrier_delay_query_start | username=%s | timeout_seconds=%s",
            current_user["username"],
            connection.timeout,
        )
        print("Dashboard: starting airline delay chart query", flush=True)
        cursor.execute(
            """
            SELECT
                airline.airline_name,
                AVG(CAST(arrival_delay_minutes AS FLOAT)) AS average_arrival_delay
            FROM dbo.FlightInstance AS flight
            INNER JOIN dbo.Airline AS airline
                ON airline.carrier_code = flight.carrier_code
            WHERE flight.arrival_delay_minutes IS NOT NULL
            GROUP BY airline.carrier_code, airline.airline_name
            ORDER BY airline.airline_name
            """
        )
        carrier_delays = cursor.fetchall()
        elapsed = perf_counter() - stage_started
        logger.info(
            "dashboard_carrier_delay_query_complete | username=%s | "
            "airline_count=%s | elapsed_seconds=%.3f",
            current_user["username"],
            len(carrier_delays),
            elapsed,
        )
        print(
            f"Dashboard: airline delay chart query completed in {elapsed:.2f}s "
            f"({len(carrier_delays)} airlines)",
            flush=True,
        )
    except Exception as exc:
        elapsed = perf_counter() - stage_started
        print(
            f"Dashboard: failed during {stage} after {elapsed:.2f}s: {exc}",
            flush=True,
        )
        logger.exception(
            "dashboard_query_failed | username=%s | stage=%s | elapsed_seconds=%.3f",
            current_user["username"],
            stage,
            elapsed,
        )
        raise HTTPException(
            status_code=503,
            detail="Dashboard insights are temporarily unavailable. Check the SQL Server connection and try again.",
        ) from exc
    finally:
        if connection is not None:
            connection.close()

    result = {
        "metrics": {
            "total_flights": int(metrics[0]),
            "total_carriers": int(metrics[1]),
            "total_airports": int(metrics[2]),
            "average_arrival_delay": (
                round(float(metrics[3]), 1) if metrics[3] is not None else None
            ),
            "average_departure_delay": (
                round(float(metrics[4]), 1) if metrics[4] is not None else None
            ),
            "on_time_arrival_percentage": (
                round(float(metrics[5]), 1) if metrics[5] is not None else None
            ),
        },
        "carrier_delays": [
            {"airline_name": row[0].strip(), "average_delay": round(float(row[1]), 1)}
            for row in carrier_delays
        ],
    }
    response.headers["X-Dashboard-Cache"] = "MISS"
    with _dashboard_cache_lock:
        _dashboard_cache = deepcopy(result)
        _dashboard_cache_expires_at = (
            perf_counter() + settings.DASHBOARD_CACHE_TTL_SECONDS
        )
    logger.info(
        "dashboard_cache_store | username=%s | ttl_seconds=%s",
        current_user["username"],
        settings.DASHBOARD_CACHE_TTL_SECONDS,
    )
    return result
