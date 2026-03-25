from datetime import datetime, timezone

def format_relative_time(epoch_ms: int) -> str:
    now = datetime.now(timezone.utc)
    then = datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc)
    delta_seconds = max(0, int((now - then).total_seconds()))

    if delta_seconds < 60:
        return "just now"
    if delta_seconds < 3600:
        minutes = delta_seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    if delta_seconds < 86400:
        hours = delta_seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    if delta_seconds < 2592000:
        days = delta_seconds // 86400
        return f"{days} day{'s' if days != 1 else ''} ago"

    months = delta_seconds // 2592000
    return f"{months} month{'s' if months != 1 else ''} ago"