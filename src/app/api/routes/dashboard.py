from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.config import settings
from app.db.connection import get_sql_server_connection
from app.logging_conf import get_logger

router = APIRouter(prefix="/api", tags=["dashboard"])
logger = get_logger("dashboard")


@router.get("/dashboard")
async def dashboard_data(current_user: dict = Depends(get_current_user)):
    connection = None
    try:
        connection = get_sql_server_connection()
        connection.timeout = settings.MAX_QUERY_SECONDS
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                (SELECT COUNT_BIG(*) FROM dbo.FlightInstance) AS total_flights,
                (SELECT COUNT_BIG(*) FROM dbo.Airline) AS total_carriers,
                (SELECT COUNT_BIG(*) FROM dbo.Airport) AS total_airports,
                (
                    SELECT AVG(CAST(arrival_delay_minutes AS FLOAT))
                    FROM dbo.FlightInstance
                    WHERE arrival_delay_minutes IS NOT NULL
                ) AS average_arrival_delay
            """
        )
        metrics = cursor.fetchone()
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
    except Exception as exc:
        logger.exception("dashboard_query_failed | username=%s", current_user["username"])
        raise HTTPException(
            status_code=503,
            detail="Dashboard insights are temporarily unavailable. Check the SQL Server connection and try again.",
        ) from exc
    finally:
        if connection is not None:
            connection.close()

    return {
        "metrics": {
            "total_flights": int(metrics[0]),
            "total_carriers": int(metrics[1]),
            "total_airports": int(metrics[2]),
            "average_arrival_delay": (
                round(float(metrics[3]), 1) if metrics[3] is not None else None
            ),
        },
        "carrier_delays": [
            {"airline_name": row[0].strip(), "average_delay": round(float(row[1]), 1)}
            for row in carrier_delays
        ],
    }
