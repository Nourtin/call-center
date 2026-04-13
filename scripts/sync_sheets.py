import sys
import os
import json
import pandas as pd
import gspread
import requests
from pathlib import Path
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

load_dotenv(dotenv_path=r"C:\Users\um6p\Documents\stage\Call_extractor\call-center-pipeline\.env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
HEADERS = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

def get_calls_from_db():
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/calls_live",
        headers=HEADERS,
        params={
            "select": "*",
            "order":  "timestamp.desc",
            "limit":  "10000"
        },
        timeout=30
    )
    r.raise_for_status()
    return r.json()

def get_or_create_sheet(tab_name: str):
    """Ouvre le sheet et crée l'onglet s'il n'existe pas."""
    creds_json = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
    creds      = Credentials.from_service_account_info(creds_json, scopes=[
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ])
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(os.environ["GOOGLE_SHEET_ID"])

    # Vérifie si l'onglet existe, sinon le crée
    existing_tabs = [ws.title for ws in sh.worksheets()]
    if tab_name not in existing_tabs:
        print(f"Onglet '{tab_name}' introuvable → création...")
        ws = sh.add_worksheet(title=tab_name, rows=10000, cols=40)
        print(f"Onglet '{tab_name}' créé !")
    else:
        ws = sh.worksheet(tab_name)
        print(f"Onglet '{tab_name}' existant trouvé.")

    return ws

def sync_to_sheets():
    print("Récupération des données depuis Supabase...")
    calls = get_calls_from_db()
    print(f"{len(calls)} appels récupérés")

    if not calls:
        print("Aucun appel à synchroniser.")
        return

    df = pd.DataFrame(calls)

    # Crée ou récupère l'onglet test
    ws = get_or_create_sheet("test2")

    # Préserve Classification/Resultat déjà remplis
    existing = ws.get_all_records()
    if existing:
        df_existing = pd.DataFrame(existing)
        if "UniqueID" in df_existing.columns:
            preserved = df_existing[["UniqueID", "Classification", "Resultat"]].copy()
            preserved = preserved[preserved["Classification"] != ""]
            if not preserved.empty:
                df = df.merge(
                    preserved,
                    left_on="unique_id",
                    right_on="UniqueID",
                    how="left",
                    suffixes=("", "_saved")
                )
                df["classification"] = df.get("Classification_saved", df["classification"]).fillna(df["classification"])
                df["resultat"]       = df.get("Resultat_saved", df["resultat"]).fillna(df["resultat"])
                df = df.drop(columns=[c for c in df.columns if c.endswith("_saved")])

    # Renomme les colonnes pour l'affichage
    df = df.rename(columns={
        "unique_id":        "UniqueID",
        "from_number":      "from_number",
        "agent_id":         "agent_id",
        "timestamp":        "Timestamp",
        "duration_seconds": "Duration_seconds",
        "callee_name":      "callee_name",
        "apellido":         "Apellido",
        "edad":             "Edad",
        "ciudad":           "Ciudad",
        "direccion":        "direccion",
        "codigo_postal":    "codigo_postal",
        "calefaccion":      "calefaccion",
        "messagerie":       "Messagerie",
        "classification":   "Classification",
        "resultat":         "Resultat",
        "recording_url":    "recording_url",
        "inserted_at":      "inserted_at",
    })

    # Écrit dans Sheets
    ws.clear()
    ws.update([df.columns.tolist()] + df.fillna("").values.tolist())
    print(f"Google Sheets mis à jour → {len(df)} lignes dans l'onglet 'test'")
def sync_to_sheets():
    print("Récupération des données depuis Supabase...")
    calls = get_calls_from_db()
    print(f"{len(calls)} appels récupérés")

    if not calls:
        print("Aucun appel à synchroniser.")
        return

    df = pd.DataFrame(calls)
    print(f"Colonnes disponibles : {df.columns.tolist()}")
    print(f"Nombre de lignes : {len(df)}")

    ws = get_or_create_sheet("test2")

    # Écrit directement sans transformation pour tester
    ws.clear()
    data = [df.columns.tolist()] + df.fillna("").values.tolist()
    print(f"Nombre de lignes à écrire : {len(data)}")
    
    ws.update(data)
    print(f"Sheets mis à jour → {len(df)} lignes")

if __name__ == "__main__":
    try:
        sync_to_sheets()
    except Exception as e:
        print(f"ERREUR: {e}")
        sys.exit(1)