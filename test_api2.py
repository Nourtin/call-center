# test_api2.py
import os
from pathlib import Path
from dotenv import load_dotenv
import requests

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

TOKEN = os.environ["CALL_API_TOKEN"]
BASE  = os.environ["CALL_API_BASE_URL"]

# Test avec différents formats d'auth
formats = [
    {"Authorization": f"Bearer {TOKEN}"},
    {"Authorization": f"Token {TOKEN}"},
    {"X-API-Key": TOKEN},
    {"api-key": TOKEN},
]

for headers in formats:
    r = requests.get(f"{BASE}/calls", headers=headers, params={"page": 1}, timeout=50)
    print(f"{list(headers.keys())[0]} → {r.status_code}")

r = requests.get(
    f"{os.environ['CALL_API_BASE_URL']}/calls",
    headers={"X-API-Key": os.environ["CALL_API_TOKEN"]},
    params={"page": 1, "per_page": 5},
    timeout=30
)
print(r.json())