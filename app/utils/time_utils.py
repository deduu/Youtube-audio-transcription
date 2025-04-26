import re

def seconds_to_hms(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds - (hours * 3600 + minutes * 60)
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

def hms_to_seconds(hms: str) -> float:
    if '.' in hms:
        t, ms = hms.split('.'); ms = float(f"0.{ms}")
    else:
        t, ms = hms, 0.0
    parts = t.split(':')
    if len(parts) == 3:
        h, m, s = parts
        return int(h)*3600 + int(m)*60 + int(s) + ms
    if len(parts) == 2:
        m, s = parts
        return int(m)*60 + int(s) + ms
    return int(parts[0]) + ms

def validate_time_format(time_str: str) -> bool:
    pattern = r'^([0-9]{1,2}:)?[0-5]?[0-9]:[0-5][0-9](\.[0-9]{1,3})?$'
    return re.match(pattern, time_str) is not None
