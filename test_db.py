# test_db3.py
from pathlib import Path
from dotenv import load_dotenv
import os, requests

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

URL = os.environ["SUPABASE_URL"]
KEY = os.environ["SUPABASE_KEY"]

r = requests.get(
    f"{URL}/rest/v1/calls_live",
    headers={"apikey": KEY, "Authorization": f"Bearer {KEY}"},
    params={"select": "unique_id", "limit": 1},
    timeout=10
)
print("Status:", r.status_code)
print("Réponse:", r.text[:200])