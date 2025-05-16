import os
from apscheduler.triggers.cron import CronTrigger

def get_cron_trigger() -> CronTrigger:
    """
    Read cron string from env, validate it via CronTrigger.
    Raises ValueError if invalid.
    """
    cron_string = os.environ.get('CRON_STRING', "*/10 * * * *")

    fields = cron_string.strip().split()
    if len(fields) != 5:
        raise ValueError(f"Invalid cron string '{cron_string}': must have exactly 5 fields")

    try:
        minute, hour, day, month, weekday = fields
        return CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=weekday
        )
    except Exception as e:
        raise ValueError(f"Invalid cron values in '{cron_string}': {e}")
