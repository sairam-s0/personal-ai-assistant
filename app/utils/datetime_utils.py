from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


FIXED_TIMEZONES = {
    "UTC": timezone.utc,
    "Asia/Kolkata": timezone(timedelta(hours=5, minutes=30), "IST"),
    "Asia/Calcutta": timezone(timedelta(hours=5, minutes=30), "IST"),
}


def get_zone(timezone_name: str):
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return FIXED_TIMEZONES.get(timezone_name, timezone.utc)


def now_local(timezone_name: str) -> datetime:
    return datetime.now(get_zone(timezone_name))


def serialize_local(dt: datetime) -> str:
    if dt.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    return dt.isoformat(timespec="seconds")


def parse_local_datetime(value: str, timezone_name: str) -> datetime:
    raw = value.strip().lower()
    zone = get_zone(timezone_name)
    current = now_local(timezone_name)

    if raw in {"now", "right now"}:
        return current

    if raw.startswith("in "):
        return _parse_relative(raw, current)

    if raw.startswith("tomorrow"):
        base = current.date() + timedelta(days=1)
        return datetime.combine(base, _parse_time_phrase(raw, default=time(9, 0)), zone)

    if raw.startswith("today"):
        base = current.date()
        parsed = datetime.combine(base, _parse_time_phrase(raw, default=current.time()), zone)
        if parsed < current:
            parsed = parsed + timedelta(days=1)
        return parsed

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            "Use ISO datetime like 2026-05-14T18:30:00 or simple phrases "
            "like 'in 20 minutes', 'today 6 PM', or 'tomorrow 9 AM'."
        ) from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=zone)
    return parsed.astimezone(zone)


def _parse_relative(raw: str, current: datetime) -> datetime:
    parts = raw.split()
    if len(parts) < 3:
        raise ValueError("Relative reminder must look like 'in 20 minutes'.")

    amount = int(parts[1])
    unit = parts[2].rstrip("s")
    if unit in {"minute", "min"}:
        return current + timedelta(minutes=amount)
    if unit in {"hour", "hr"}:
        return current + timedelta(hours=amount)
    if unit == "day":
        return current + timedelta(days=amount)
    raise ValueError("Relative reminder unit must be minutes, hours, or days.")


def _parse_time_phrase(raw: str, default: time) -> time:
    markers = [" at ", "today ", "tomorrow "]
    phrase = ""
    for marker in markers:
        if marker in raw:
            phrase = raw.split(marker, 1)[1].strip()
            break

    if not phrase:
        return default.replace(microsecond=0)

    phrase = phrase.replace(".", "").replace(" ", "")
    meridiem = None
    if phrase.endswith("am") or phrase.endswith("pm"):
        meridiem = phrase[-2:]
        phrase = phrase[:-2]

    if ":" in phrase:
        hour_text, minute_text = phrase.split(":", 1)
        hour = int(hour_text)
        minute = int(minute_text)
    else:
        hour = int(phrase)
        minute = 0

    if meridiem == "pm" and hour != 12:
        hour += 12
    if meridiem == "am" and hour == 12:
        hour = 0

    return time(hour, minute)
