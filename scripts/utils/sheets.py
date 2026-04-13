"""Google Sheets integration."""
import os
import json
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

def get_sheet(tab_name: str):
    creds_json = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
    creds      = Credentials.from_service_account_info(creds_json, scopes=SCOPES)
    gc         = gspread.authorize(creds)
    sh         = gc.open_by_key(os.environ["GOOGLE_SHEET_ID"])
    return sh.worksheet(tab_name)

def sync_to_sheets(df: pd.DataFrame, tab_name: str = "Test"):
    """
    Écrit le DataFrame dans Sheets.
    Ne touche pas aux colonnes Classification et Resultat
    déjà remplies par l'équipe.
    """
    ws = get_sheet(tab_name)

    # Récupère les données existantes pour préserver Classification/Resultat
    existing = ws.get_all_records()
    if existing:
        df_existing = pd.DataFrame(existing)
        preserved   = df_existing[["UniqueID", "Classification", "Resultat"]].copy()
        preserved   = preserved[preserved["Classification"] != ""]

        # Fusionne pour ne pas écraser ce qui est déjà rempli
        df = df.merge(preserved, on="UniqueID", how="left", suffixes=("", "_saved"))
        df["Classification"] = df["Classification_saved"].fillna(df["Classification"])
        df["Resultat"]       = df["Resultat_saved"].fillna(df["Resultat"])
        df = df.drop(columns=["Classification_saved", "Resultat_saved"])

    ws.clear()
    ws.update([df.columns.tolist()] + df.fillna("").values.tolist())
    print(f"Sheets mis à jour → {len(df)} lignes")