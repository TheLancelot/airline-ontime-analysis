from __future__ import annotations

from copy import deepcopy

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.logging_conf import get_logger

router = APIRouter(prefix="/api", tags=["dashboard"])
logger = get_logger("dashboard")

DASHBOARD_SNAPSHOT = {
    "metrics": {
        "total_flights": 3_401_526,
        "total_carriers": 14,
        "total_airports": 180,
        "average_arrival_delay": 7.08507916740898,
        "average_departure_delay": 15.293786671041174,
        "on_time_arrival_percentage": 76.8957,
    },
    "carrier_delays": [
        {"airline_name": "Alaska Airlines", "average_delay": 1.0233073292882597},
        {"airline_name": "American Airlines", "average_delay": 12.352459566727093},
        {"airline_name": "Delta Air Lines", "average_delay": 4.625783854506747},
        {"airline_name": "Frontier Airlines", "average_delay": 11.32045858559835},
        {"airline_name": "JetBlue Airways", "average_delay": 7.098876950005749},
        {"airline_name": "Southwest Airlines", "average_delay": 6.638628810093749},
        {"airline_name": "United Airlines", "average_delay": 4.061945863597871},
    ],
    "snapshot_note": (
        "Exact values from the current static AirlinesProject dataset. "
        "Refresh this snapshot if the database data changes."
    ),
}


@router.get("/dashboard")
async def dashboard_data(current_user: dict = Depends(get_current_user)):
    logger.info("dashboard_snapshot_served | username=%s", current_user["username"])
    return deepcopy(DASHBOARD_SNAPSHOT)
