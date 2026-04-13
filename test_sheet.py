# test_sheets.py
from pathlib import Path
from dotenv import load_dotenv
import os, json, gspread
from google.oauth2.service_account import Credentials

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

creds_json = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
creds      = Credentials.from_service_account_info(creds_json, scopes=[
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
])
gc = gspread.authorize(creds)
sh = gc.open_by_key(os.environ["GOOGLE_SHEET_ID"])
ws = sh.worksheet("Test")  # ou le nom de ton onglet

# Écrit les headers
headers = [
    "UniqueID", "from_number", "agent_id", "Timestamp", "Duration_seconds",
    "callee_name", "Apellido", "Edad", "direccion", "Ciudad",
    "codigo_postal", "status", "recording_url",
    "Classification", "Resultat"
]

ws.clear()
ws.append_row(headers)
print("Headers écrits avec succès !")

# Écrit une ligne de test
test_row = [
    "test-123", "612345678", "agent-001", "2026-04-13", 45,
    "", "", "", "", "",
    "", "completed", "https://exemple.com/recording.ogg",
    "", ""
]
ws.append_row(test_row)
print("Ligne de test insérée !")