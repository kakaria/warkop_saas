# tenants/time.py

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo


def get_business_day_boundary(
    *,
    timezone_name: str,
    business_date: date,
) -> tuple[datetime, datetime]:
    tz = ZoneInfo(timezone_name)

    local_start = datetime.combine(
        business_date,
        time.min,
        tzinfo=tz,
    )

    local_end = datetime.combine(
        business_date + timedelta(days=1),
        time.min,
        tzinfo=tz,
    )

    return (
        local_start.astimezone(timezone.utc),
        local_end.astimezone(timezone.utc),
    )


def get_business_date(
    *,
    timezone_name: str,
    now: datetime,
) -> date:
    tz = ZoneInfo(timezone_name)

    return now.astimezone(tz).date()
