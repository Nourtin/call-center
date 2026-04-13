"""API client for fetching call data."""
import os
from pathlib import Path
from dotenv import load_dotenv
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv(dotenv_path=r"C:\Users\um6p\Documents\stage\Call_extractor\call-center-pipeline\.env")

API_BASE  = os.environ["CALL_API_BASE_URL"]
API_TOKEN = os.environ["CALL_API_TOKEN"]

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def fetch_page(cursor=None):
    params = {"limit": 100}
    if cursor:
        params["cursor"] = cursor

    r = requests.get(
        f"{API_BASE}/calls",
        headers={"X-API-Key": API_TOKEN},
        params=params,
        timeout=30
    )
    r.raise_for_status()
    return r.json()

def fetch_all_calls(from_dt=None, to_dt=None, max_pages=20):
    """Récupère les appels avec limite de pages pour éviter boucle infinie."""
    all_calls  = []
    cursor     = None
    page_count = 0

    while page_count < max_pages:
        data   = fetch_page(cursor)
        calls  = data.get("data", [])

        if not calls:
            break

        all_calls.extend(calls)
        page_count += 1

        next_cursor = data.get("next_cursor")
        print(f"Page {page_count} → {len(calls)} appels | cursor: {next_cursor}")

        if not next_cursor:
            break

        # Si même cursor que avant → boucle infinie, on arrête
        if next_cursor == cursor:
            print("Cursor identique détecté → arrêt")
            break

        cursor = next_cursor

    print(f"API → {len(all_calls)} appels récupérés en {page_count} pages")
    return all_calls

def fetch_api_count(from_dt=None, to_dt=None):
    """Retourne juste le count de la première page."""
    data = fetch_page(cursor=None)
    return len(data.get("data", []))