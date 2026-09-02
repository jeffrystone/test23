from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_TIMEZONE = "Europe/Moscow"
_MSK_UTC_OFFSET = timezone(timedelta(hours=3))


def _get_timezone(tz: str):
    try:
        return ZoneInfo(tz)
    except ZoneInfoNotFoundError:
        if tz == DEFAULT_TIMEZONE:
            return _MSK_UTC_OFFSET
        raise


def get_time_greeting(
    now: datetime | None = None,
    tz: str = DEFAULT_TIMEZONE,
) -> str:
    tzinfo = _get_timezone(tz)
    local_now = (now or datetime.now(tzinfo)).astimezone(tzinfo)
    hour = local_now.hour

    if 5 <= hour < 12:
        return "Доброе утро!"
    if 12 <= hour < 18:
        return "Добрый день!"
    return "Добрый вечер!"
