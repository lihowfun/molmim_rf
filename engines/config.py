import os


def get_api_base() -> str:
    return os.environ.get("MOLMIM_API_BASE", "http://127.0.0.1:8000").rstrip("/")


API_BASE = get_api_base()
DECODE = f"{API_BASE}/decode"
HIDDEN = f"{API_BASE}/hidden"
HEADERS = {"accept": "application/json", "Content-Type": "application/json"}
