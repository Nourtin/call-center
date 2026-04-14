import os
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv(dotenv_path=r"C:\call-center-pipeline\.env")

API_BASE  = os.environ["CALL_API_BASE_URL"]
API_TOKEN = os.environ["CALL_API_TOKEN"]

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def fetch_page(cursor=None, from_dt=None, to_dt=None, to_number=None):
    params = {
        "include_variable_values": "true",  # ← clé manquante
        "limit": 100,
    }
    if cursor:
        params["cursor"] = cursor
    if from_dt:
        params["start_time_gt"] = from_dt
    if to_dt:
        params["start_time_lt"] = to_dt
    if to_number:
        params["to_number"] = to_number

    r = requests.get(
        f"{API_BASE}/calls",
        headers={"X-Api-Key": API_TOKEN},  # ← X-Api-Key pas X-API-Key
        params=params,
        timeout=30
    )
    r.raise_for_status()
    return r.json()

def fetch_all_calls(from_dt=None, to_dt=None, to_number=None, max_pages=20):
    all_calls  = []
    cursor     = None
    page_count = 0

    while page_count < max_pages:
        data  = fetch_page(cursor, from_dt, to_dt, to_number)
        calls = data.get("data", [])

        if not calls:
            print("Fin des données.")
            break

        all_calls.extend(calls)
        page_count += 1

        next_cursor = data.get("next_cursor") or data.get("cursor")
        print(f"Page {page_count} → {len(calls)} appels | cursor: {next_cursor}")

        if not next_cursor or next_cursor == cursor:
            break

        cursor = next_cursor
        time.sleep(0.1)

    print(f"API → {len(all_calls)} appels récupérés en {page_count} pages")
    return all_calls

def fetch_api_count(from_dt=None, to_dt=None):
    data = fetch_page(from_dt=from_dt, to_dt=to_dt)
    return len(data.get("data", []))