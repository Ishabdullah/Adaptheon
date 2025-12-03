from datetime import datetime


def get_now():
    """
    Return current local time info from the device clock.
    """
    now = datetime.now()
    return {
        "iso": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
    }
