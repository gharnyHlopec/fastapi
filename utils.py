from datetime import datetime, timezone

def get_current_strfdatetime() -> str:
    current_datetime = datetime.now(timezone.utc)
    return current_datetime.strftime("%d-%m-%Y %H-%M-%S")