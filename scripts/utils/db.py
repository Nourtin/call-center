import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=r"C:\Users\um6p\Documents\stage\Call_extractor\call-center-pipeline\.env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

HEADERS = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type":  "application/json",
    "Prefer":        "resolution=ignore-duplicates"
}

def insert_call(row: dict) -> bool:
    """Insère un appel via l'API REST Supabase."""
    payload = {
        "unique_id":                   row.get("UniqueID", ""),
        "from_number":                 row.get("from_number", ""),
        "agent_id":                    row.get("agent_id", ""),
        "timestamp":                   row.get("Timestamp"),
        "duration_seconds":            row.get("Duration_seconds", 0),
        "callee_name":                 row.get("callee_name", ""),
        "apellido":                    row.get("Apellido", ""),
        "edad":                        row.get("Edad", ""),
        "direccion":                   row.get("direccion", ""),
        "ciudad":                      row.get("Ciudad", ""),
        "codigo_postal":               row.get("codigo_postal", ""),
        "adress_origine":              row.get("adress_origine", ""),
        "code_postal":                 row.get("code_postal", ""),
        "tipo_vivienda":               row.get("tipo_vivienda", ""),
        "superfici_vivienda":          row.get("superfici_vivienda", ""),
        "superfici_desvan":            row.get("superfici_desvan", ""),
        "estado_desvan":               row.get("estado_desvan", ""),
        "accesso_desvan":              row.get("accesso_desvan", ""),
        "tiene_desvan":                row.get("tiene_desvan", ""),
        "calefaccion":                 row.get("calefaccion", ""),
        "suelo":                       row.get("suelo", ""),
        "altura":                      row.get("altura", ""),
        "piso_casa":                   row.get("piso_casa", ""),
        "proprietad":                  row.get("proprietad", ""),
        "disponibilidad_visita":       row.get("disponibilidad_visita", ""),
        "disponibilidad_llamada":      row.get("disponibilidad_llamada", ""),
        "debe_ser_llamado_de_nuevo":   row.get("debe_ser_llamado_de_nuevo", ""),
        "resumen_conversacion":        row.get("resumen_conversacion", ""),
        "other_extract":               row.get("other_extract", ""),
        "messagerie":                  row.get("Messagerie", ""),
        "classification":              row.get("Classification", ""),
        "resultat":                    row.get("Resultat", ""),
        "list_name":                   row.get("list_name", ""),
        "url":                         row.get("url", ""),
        "recording_url":               row.get("recording_url", ""),
    }

    # Retire les valeurs None
    payload = {k: v for k, v in payload.items() if v is not None}

    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/calls_live",
        headers=HEADERS,
        json=payload,
        timeout=15
    )

    if r.status_code in (200, 201):
        return True
    elif r.status_code == 409:
        return False  # doublon ignoré
    else:
        print(f"Erreur insertion: {r.status_code} → {r.text}")
        return False

def get_db_count(from_dt=None, to_dt=None) -> int:
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/calls_live",
        headers={**HEADERS, "Prefer": "count=exact"},
        params={"select": "unique_id"},
        timeout=15
    )
    count = int(r.headers.get("content-range", "0/0").split("/")[-1])
    return count

def save_audit(run_id, script, period_from, period_to,
               api_declared=0, api_fetched=0, after_filter=0,
               inserted=0, ignored=0, error=None):
    payload = {
        "run_id":        run_id,
        "script":        script,
        "period_from":   period_from,
        "period_to":     period_to,
        "api_declared":  api_declared,
        "api_fetched":   api_fetched,
        "after_filter":  after_filter,
        "inserted_in_db": inserted,
        "ignored_in_db": ignored,
        "error_message": error
    }
    requests.post(
        f"{SUPABASE_URL}/rest/v1/pipeline_audit",
        headers=HEADERS,
        json=payload,
        timeout=15
    )