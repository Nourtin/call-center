import requests
import time
import random
import psycopg2
import os
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
API_KEY = os.getenv("CALL_API_TOKEN", "R9PhYFJkBlguePJlpj8Y9ArmxDkGy9TS")
POSTGRES_CONN = os.getenv("POSTGRES_CONN")
# Format attendu dans .env :
# POSTGRES_CONN=postgresql://postgres:[MOT_DE_PASSE]@db.eioitlkuyfjqlgeoqryp.supabase.co:5432/postgres

URL = "https://api.callrounded.com/v1/calls"
START_TIME = "2026-04-08T11:00:00Z"
END_TIME = "2026-04-08T13:00:00Z"
TO_NUMBER = "+33974994331"
TABLE_NAME = "appels"

# Colonnes définitives (une seule version, tout en minuscules sauf les noms métier)
COLUMNS = [
    "resumen_conversacion", "other_extract", "callee_name", "apellido",
    "direccion", "ciudad", "codigo_postal", "adress_origine", "code_postal",
    "from_number", "tipo_vivienda", "superfici_vivienda", "superfici_desvan",
    "estado_desvan", "accesso_desvan", "calefaccion", "disponibilidad_visita",
    "disponibilidad_llamada", "suelo", "altura", "proprietad", "url",
    "list_name", "timestamp", "duration_seconds", "edad", "uniqueid",
    "agent_id", "tiene_desvan", "debe_ser_llamado_de_nuevo", "piso_casa",
    "messagerie", "classification", "resultat"
]


def get_db_connection():
    """Connexion directe PostgreSQL à Supabase."""
    if not POSTGRES_CONN:
        raise ValueError(
            "❌ POSTGRES_CONN n'est pas défini dans le .env\n"
            "   → Va dans Supabase > Settings > Database > Connection string > URI\n"
            "   → Ajoute dans .env : POSTGRES_CONN=postgresql://postgres:[MOT_DE_PASSE]@db.eioitlkuyfjqlgeoqryp.supabase.co:5432/postgres"
        )
    conn = psycopg2.connect(POSTGRES_CONN)
    print("✅ Connecté à Supabase (PostgreSQL direct)")
    return conn


def recreate_table():
    """Recrée la table avec un schéma propre (tout en minuscules, sans doublons)."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(f"DROP TABLE IF EXISTS {TABLE_NAME} CASCADE;")
        print("🗑️  Ancienne table supprimée")

        create_query = f"""
        CREATE TABLE {TABLE_NAME} (
            id                      SERIAL PRIMARY KEY,
            resumen_conversacion    TEXT,
            other_extract           TEXT,
            callee_name             TEXT,
            apellido                TEXT,
            direccion               TEXT,
            ciudad                  TEXT,
            codigo_postal           TEXT,
            adress_origine          TEXT,
            code_postal             TEXT,
            from_number             TEXT,
            tipo_vivienda           TEXT,
            superfici_vivienda      TEXT,
            superfici_desvan        TEXT,
            estado_desvan           TEXT,
            accesso_desvan          TEXT,
            calefaccion             TEXT,
            disponibilidad_visita   TEXT,
            disponibilidad_llamada  TEXT,
            suelo                   TEXT,
            altura                  TEXT,
            proprietad              TEXT,
            url                     TEXT,
            list_name               TEXT,
            timestamp               TIMESTAMPTZ,
            duration_seconds        INTEGER,
            edad                    TEXT,
            uniqueid                TEXT UNIQUE,
            agent_id                TEXT,
            tiene_desvan            TEXT,
            debe_ser_llamado_de_nuevo TEXT,
            piso_casa               TEXT,
            messagerie              TEXT,
            classification          TEXT,
            resultat                TEXT,
            created_at              TIMESTAMPTZ DEFAULT NOW()
        );
        """
        cursor.execute(create_query)
        conn.commit()
        print(f"✅ Table '{TABLE_NAME}' créée avec succès")

    except Exception as e:
        print(f"❌ Erreur création table : {e}")
        raise
    finally:
        if conn:
            cursor.close()
            conn.close()


def fetch_all_calls():
    """Récupère tous les appels via pagination curseur."""
    all_calls = []
    current_cursor = None
    headers = {"X-Api-Key": API_KEY}

    print(f"\n🚀 Extraction pour {TO_NUMBER}")
    print(f"   Période : {START_TIME} → {END_TIME}\n")

    while True:
        params = {
            "start_time_gt": START_TIME,
            "start_time_lt": END_TIME,
            "to_number": TO_NUMBER,
            "include_variable_values": "true",
            "limit": 100,
        }
        if current_cursor:
            params["cursor"] = current_cursor

        try:
            response = requests.get(URL, headers=headers, params=params, timeout=100)

            if response.status_code != 200:
                print(f"❌ API Error {response.status_code} : {response.text}")
                break

            data = response.json()
            calls = data.get("data", [])

            if not calls:
                print("🏁 Fin des données")
                break

            all_calls.extend(calls)
            print(f"📥 {len(all_calls)} appels récupérés...")

            current_cursor = data.get("next_cursor") or data.get("cursor")
            if not current_cursor:
                break

            time.sleep(0.1)

        except Exception as e:
            print(f"❌ Erreur fetch : {e}")
            break

    return all_calls


def build_record(call):
    """Construit un tuple correspondant à COLUMNS à partir d'un appel brut."""
    vars_dict = {v["name"]: v["value"] for v in call.get("variable_values", [])}
    from_num = str(call.get("from_number", ""))

    # Durée : cast sécurisé
    try:
        duration = int(call.get("duration_seconds") or 0)
    except (ValueError, TypeError):
        duration = 0

    # UniqueID unique et déterministe (basé sur l'ID de l'appel si disponible)
    call_id = call.get("id") or call.get("call_id") or ""
    unique_id = f"CALL-{call_id}" if call_id else f"ID-{random.randint(10**9, 10**10)}{int(time.time()*1000)}"

    # URL réelle (pas une formule Excel)
    url = f"http://37.59.222.18/RECORDINGS/MP3/{from_num}-all.mp3"

    # Timestamp : None si absent (colonne TIMESTAMPTZ)
    timestamp = call.get("start_time") or None

    values = {
        "resumen_conversacion":    vars_dict.get("resumen_conversacion") or "",
        "other_extract":           vars_dict.get("other_extract") or "",
        "callee_name":             vars_dict.get("callee_name") or call.get("callee_name") or "",
        "apellido":                vars_dict.get("Apellido") or vars_dict.get("apellido") or "",
        "direccion":               vars_dict.get("direccion") or "",
        "ciudad":                  vars_dict.get("Ciudad") or vars_dict.get("ciudad") or "",
        "codigo_postal":           vars_dict.get("codigo_postal") or "",
        "adress_origine":          vars_dict.get("adress_origine") or "",
        "code_postal":             vars_dict.get("code_postal") or "",
        "from_number":             from_num,
        "tipo_vivienda":           vars_dict.get("tipo_vivienda") or "",
        "superfici_vivienda":      vars_dict.get("superfici_vivienda") or "",
        "superfici_desvan":        vars_dict.get("superfici_desvan") or "",
        "estado_desvan":           vars_dict.get("estado_desvan") or "",
        "accesso_desvan":          vars_dict.get("accesso_desvan") or "",
        "calefaccion":             vars_dict.get("calefaccion") or "",
        "disponibilidad_visita":   vars_dict.get("disponibilidad_visita") or "",
        "disponibilidad_llamada":  vars_dict.get("disponibilidad_llamada") or "",
        "suelo":                   vars_dict.get("suelo") or "",
        "altura":                  vars_dict.get("altura") or "",
        "proprietad":              vars_dict.get("proprietad") or "",
        "url":                     url,
        "list_name":               vars_dict.get("list_name") or call.get("list_name") or "",
        "timestamp":               timestamp,
        "duration_seconds":        duration,
        "edad":                    vars_dict.get("Edad") or vars_dict.get("edad") or "",
        "uniqueid":                unique_id,
        "agent_id":                str(call.get("agent_id") or ""),
        "tiene_desvan":            vars_dict.get("tiene_desvan") or "",
        "debe_ser_llamado_de_nuevo": vars_dict.get("debe_ser_llamado_de_nuevo") or "",
        "piso_casa":               vars_dict.get("piso_casa") or "",
        "messagerie":              vars_dict.get("Messagerie") or vars_dict.get("messagerie") or "",
        "classification":          "",
        "resultat":                "",
    }

    return tuple(values[col] for col in COLUMNS)


def save_to_supabase(calls):
    """Insère les appels en base, ignore les doublons sur uniqueid."""
    if not calls:
        print("⚠️  Aucun appel à sauvegarder")
        return

    print(f"\n💾 Sauvegarde de {len(calls)} appels...")

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        records = [build_record(call) for call in calls]

        columns_str = ", ".join(COLUMNS)
        insert_query = f"""
            INSERT INTO {TABLE_NAME} ({columns_str})
            VALUES %s
            ON CONFLICT (uniqueid) DO NOTHING
        """

        execute_values(cursor, insert_query, records)
        conn.commit()

        print(f"✅ {len(records)} appels insérés (doublons ignorés automatiquement)")

    except Exception as e:
        print(f"❌ Erreur insertion : {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            cursor.close()
            conn.close()


def main():
    print("=" * 55)
    print("  Sync CallRounded → Supabase")
    print("=" * 55)

    # Vérification POSTGRES_CONN avant tout
    if not POSTGRES_CONN:
        print("\n❌ POSTGRES_CONN manquant dans .env")
        print("   Ajoute cette ligne dans ton fichier .env :")
        print("   POSTGRES_CONN=postgresql://postgres:[MOT_DE_PASSE]@db.eioitlkuyfjqlgeoqryp.supabase.co:5432/postgres")
        print("\n   → Dashboard Supabase > Settings > Database > Connection string > URI")
        return

    # Étape 1 : (Re)créer la table proprement
    print("\n📌 Étape 1 : Recréation de la table")
    recreate_table()

    # Étape 2 : Récupérer les appels
    print("\n📌 Étape 2 : Extraction CallRounded")
    calls = fetch_all_calls()
    print(f"\n📊 Total récupéré : {len(calls)} appels")

    # Étape 3 : Insérer
    print("\n📌 Étape 3 : Insertion Supabase")
    if calls:
        save_to_supabase(calls)
    else:
        print("⚠️  Aucun appel trouvé dans la période donnée")

    print("\n✨ Terminé !")


if __name__ == "__main__":
    main()