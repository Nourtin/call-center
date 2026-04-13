# test_api.py à la racine
import os
from pathlib import Path
from dotenv import load_dotenv
import requests

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

r = requests.get(
    f"{os.environ['CALL_API_BASE_URL']}/calls",
    headers={"Authorization": f"Bearer {os.environ['CALL_API_TOKEN']}"},
    params={"page": 1, "per_page": 5},
    timeout=30
)

print("Status:", r.status_code)
print("Réponse:", r.text[:500])