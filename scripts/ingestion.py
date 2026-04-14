import requests
import time
import random
import psycopg2
import os
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("CALL_API_TOKEN", "R9PhYFJkBlguePJlpj8Y9ArmxDkGy9TS")
POSTGRES_CONN = os.getenv("POSTGRES_CONN")
URL = "https://api.callrounded.com/v1/calls"
START_TIME = "2026-04-09T11:00:00Z"
END_TIME = "2026-04-09T13:00:00Z"
TO_NUMBER = "+33974994331"
TABLE_NAME = "appels"


def get_db_connection():
    if not POSTGRES_CONN:
        raise ValueError("POSTGRES_CONN est vide ! Vérifie ton fichier .env")
    try:
        conn = psycopg2.connect(POSTGRES_CONN, connect_timeout=10)
        print("✅ Connecté à Supabase!")
        return conn
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        print(f"   → POSTGRES_CONN utilisé: {POSTGRES_CONN[:40]}...")  # Debug
        raise


def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {TABLE_NAME} CASCADE;")
        cursor.execute(f"""
        CREATE TABLE {TABLE_NAME} (
            id SERIAL PRIMARY KEY,
            resumen_conversacion TEXT,
            other_extract TEXT,
            callee_name TEXT,
            "Apellido" TEXT,
            direccion TEXT,
            "Ciudad" TEXT,
            codigo_postal TEXT,
            adress_origine TEXT,
            code_postal TEXT,
            from_number TEXT,
            tipo_vivienda TEXT,
            superfici_vivienda TEXT,
            superfici_desvan TEXT,
            estado_desvan TEXT,
            accesso_desvan TEXT,
            calefaccion TEXT,
            disponibilidad_visita TEXT,
            disponibilidad_llamada TEXT,
            suelo TEXT,
            altura TEXT,
            proprietad TEXT,
            url TEXT,
            list_name TEXT,
            "Timestamp" TEXT,
            "Duration_seconds" INTEGER,
            "Edad" TEXT,
            "UniqueID" TEXT UNIQUE,
            agent_id TEXT,
            tiene_desvan TEXT,
            debe_ser_llamado_de_nuevo TEXT,
            piso_casa TEXT,
            "Messagerie" TEXT,
            "Classification" TEXT DEFAULT '',
            "Resultat" TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)
        conn.commit()
        print(f"✅ Table '{TABLE_NAME}' créée!")
    finally:
        cursor.close()
        conn.close()


def fetch_all_calls():
    all_calls = []
    current_cursor = None
    headers = {"X-Api-Key": API_KEY}
    page = 1

    print(f"🚀 Extraction pour {TO_NUMBER} | {START_TIME} → {END_TIME}\n")

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
            response = requests.get(URL, headers=headers, params=params, timeout=30)
            if response.status_code != 200:
                print(f"❌ API Error {response.status_code}: {response.text}")
                break

            data = response.json()
            calls = data.get("data", [])

            if not calls:
                print("🏁 Fin des données (page vide reçue)")
                break

            all_calls.extend(calls)
            print(f"   Page {page} → +{len(calls)} appels | Total: {len(all_calls)}")

            # ✅ FIX : on essaie TOUS les champs cursor possibles
            current_cursor = (
                data.get("next_cursor")
                or data.get("nextCursor")
                or data.get("cursor")
                or data.get("meta", {}).get("next_cursor")
            )

            if not current_cursor:
                print("🏁 Fin de pagination (plus de cursor)")
                break

            page += 1
            time.sleep(0.15)

        except requests.Timeout:
            print(f"⏱️ Timeout page {page}, retry dans 2s...")
            time.sleep(2)
        except Exception as e:
            print(f"❌ Erreur page {page}: {e}")
            break

    return all_calls


def build_records(calls):
    records = []
    columns = [
        "resumen_conversacion", "other_extract", "callee_name", "Apellido", "direccion",
        "Ciudad", "codigo_postal", "adress_origine", "code_postal", "from_number",
        "tipo_vivienda", "superfici_vivienda", "superfici_desvan", "estado_desvan",
        "accesso_desvan", "calefaccion", "disponibilidad_visita", "disponibilidad_llamada",
        "suelo", "altura", "proprietad", "url", "list_name", "Timestamp",
        "Duration_seconds", "Edad", "UniqueID", "agent_id", "tiene_desvan",
        "debe_ser_llamado_de_nuevo", "piso_casa", "Messagerie", "Classification", "Resultat"
    ]

    for call in calls:
        v = {item["name"]: item["value"] for item in call.get("variable_values", [])}
        from_num = str(call.get("from_number", ""))
        unique_id = f"ID-{random.randint(10**9, 10**10 - 1)}{int(time.time() * 1000)}"

        row = (
            v.get("resumen_conversacion", ""),
            v.get("other_extract", ""),
            v.get("callee_name") or call.get("callee_name", ""),
            v.get("Apellido", ""),
            v.get("direccion", ""),
            v.get("Ciudad", ""),
            v.get("codigo_postal", ""),
            v.get("adress_origine", ""),
            v.get("code_postal", ""),
            from_num,
            v.get("tipo_vivienda", ""),
            v.get("superfici_vivienda", ""),
            v.get("superfici_desvan", ""),
            v.get("estado_desvan", ""),
            v.get("accesso_desvan", ""),
            v.get("calefaccion", ""),
            v.get("disponibilidad_visita", ""),
            v.get("disponibilidad_llamada", ""),
            v.get("suelo", ""),
            v.get("altura", ""),
            v.get("proprietad", ""),
            f"http://37.59.222.18/RECORDINGS/MP3/{from_num}-all.mp3",
            v.get("list_name") or call.get("list_name", ""),
            call.get("start_time", ""),
            int(call.get("duration_seconds", 0) or 0),
            v.get("Edad", ""),
            unique_id,
            str(call.get("agent_id", "")),
            v.get("tiene_desvan", ""),
            v.get("debe_ser_llamado_de_nuevo", ""),
            v.get("piso_casa", ""),
            v.get("Messagerie", ""),
            "",  # Classification
            "",  # Resultat
        )
        records.append(row)

    return columns, records


def save_to_supabase(calls):
    if not calls:
        print("⚠️ Aucun appel à sauvegarder")
        return

    print(f"\n💾 Sauvegarde de {len(calls)} appels...")
    columns, records = build_records(calls)

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Colonnes avec majuscules entre guillemets
        cols_str = ", ".join([f'"{c}"' if c[0].isupper() else c for c in columns])
        query = f"""
            INSERT INTO {TABLE_NAME} ({cols_str})
            VALUES %s
            ON CONFLICT ("UniqueID") DO NOTHING
        """
        execute_values(cursor, query, records, page_size=200)
        conn.commit()
        print(f"✅ {len(records)} appels sauvegardés!")
    except Exception as e:
        conn.rollback()
        print(f"❌ Erreur insertion: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def main():
    print("🔄 Synchronisation CallRounded → Supabase\n")

    if not POSTGRES_CONN:
        print("❌ POSTGRES_CONN manquant dans .env !")
        print("   Format attendu: postgresql://postgres.[ref]:[password]@aws-0-xx.pooler.supabase.com:6543/postgres")
        return

    create_table()
    calls = fetch_all_calls()
    print(f"\n📊 Total récupéré: {len(calls)} appels")

    if calls:
        save_to_supabase(calls)

    print("\n✨ Terminé!")


if __name__ == "__main__":
    main()