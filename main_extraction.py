import requests
import time
import random
import os
from dotenv import load_dotenv
from pathlib import Path


# ==============================
# 🔐 LOAD ENV
# ==============================
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Debug (optionnel)
print("URL:", SUPABASE_URL)
print("KEY:", SUPABASE_KEY[:10] if SUPABASE_KEY else None)

# ==============================
# 🔗 SUPABASE CLIENT
# ==============================
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==============================
# 📡 API CONFIG
# ==============================
API_KEY = "R9PhYFJkBlguePJlpj8Y9ArmxDkGy9TS"
URL = "https://api.callrounded.com/v1/calls"
START_TIME = "2026-04-08T11:00:00Z"
END_TIME = "2026-04-08T13:00:00Z"
TO_NUMBER = "+33974994331"

# ==============================
# 🚀 EXTRACTION + INSERTION
# ==============================
def extraire_et_envoyer():
    all_calls = []
    current_cursor = None
    headers = {"X-Api-Key": API_KEY}

    print(f"🚀 Extraction pour {TO_NUMBER}...")

    # ==========================
    # 📥 EXTRACTION API
    # ==========================
    while True:
        params = {
            "start_time_gt": START_TIME,
            "start_time_lt": END_TIME,
            "to_number": TO_NUMBER,
            "include_variable_values": "true",
            "limit": 100
        }

        if current_cursor:
            params["cursor"] = current_cursor

        try:
            response = requests.get(URL, headers=headers, params=params)

            if response.status_code != 200:
                print(f"❌ Erreur API : {response.status_code}")
                print(response.text)
                break

            data = response.json()
            calls = data.get("data", [])

            if not calls:
                print("🏁 Fin des données.")
                break

            all_calls.extend(calls)
            print(f"📥 {len(all_calls)} appels récupérés...")

            current_cursor = data.get("next_cursor") or data.get("cursor")

            if not current_cursor:
                break

            time.sleep(0.1)

        except Exception as e:
            print(f"❌ Erreur : {e}")
            break

    # ==========================
    # 📤 INSERTION SUPABASE
    # ==========================
    if all_calls:
        print("🚀 Insertion dans Supabase...")

        batch = []

        for c in all_calls:
            vars_dict = {v['name']: v['value'] for v in c.get('variable_values', [])}
            from_num = str(c.get('from_number', ''))

            unique_id = f"ID-{random.randint(1000000000, 9999999999)}{int(time.time()*1000)}"

            row = {
                "resumen_conversacion": vars_dict.get("resumen_conversacion", ""),
                "other_extract": vars_dict.get("other_extract", ""),
                "callee_name": vars_dict.get("callee_name") or c.get("callee_name", ""),
                "Apellido": vars_dict.get("Apellido", ""),
                "direccion": vars_dict.get("direccion", ""),
                "Ciudad": vars_dict.get("Ciudad", ""),
                "codigo_postal": vars_dict.get("codigo_postal", ""),
                "adress_origine": vars_dict.get("adress_origine", ""),
                "code_postal": vars_dict.get("code_postal", ""),
                "from_number": from_num,
                "tipo_vivienda": vars_dict.get("tipo_vivienda", ""),
                "superfici_vivienda": vars_dict.get("superfici_vivienda", ""),
                "superfici_desvan": vars_dict.get("superfici_desvan", ""),
                "estado_desvan": vars_dict.get("estado_desvan", ""),
                "accesso_desvan": vars_dict.get("accesso_desvan", ""),
                "calefaccion": vars_dict.get("calefaccion", ""),
                "disponibilidad_visita": vars_dict.get("disponibilidad_visita", ""),
                "disponibilidad_llamada": vars_dict.get("disponibilidad_llamada", ""),
                "suelo": vars_dict.get("suelo", ""),
                "altura": vars_dict.get("altura", ""),
                "proprietad": vars_dict.get("proprietad", ""),
                "url": f"http://37.59.222.18/RECORDINGS/MP3/{from_num}-all.mp3",
                "list_name": vars_dict.get("list_name") or c.get("list_name", ""),
                "Timestamp": c.get("start_time", ""),
                "Duration_seconds": c.get("duration_seconds", 0),
                "Edad": vars_dict.get("Edad", ""),
                "UniqueID": unique_id,
                "agent_id": c.get("agent_id", ""),
                "tiene_desvan": vars_dict.get("tiene_desvan", ""),
                "debe_ser_llamado_de_nuevo": vars_dict.get("debe_ser_llamado_de_nuevo", ""),
                "piso_casa": vars_dict.get("piso_casa", ""),
                "Messagerie": vars_dict.get("Messagerie", ""),
                "Classification": "",
                "Resultat": ""
            }

            batch.append(row)

            # Insert par batch de 100
            if len(batch) == 100:
                supabase.table("appels").insert(batch).execute()
                print("✅ 100 lignes insérées")
                batch = []

        # Insert le reste
        if batch:
            supabase.table("appels").insert(batch).execute()
            print(f"✅ {len(batch)} lignes restantes insérées")

        print(f"\n🎉 TERMINÉ : {len(all_calls)} appels envoyés dans Supabase")

    else:
        print("⚠ Aucun appel trouvé")

# ==============================
# ▶️ RUN
# ==============================
if __name__ == "__main__":
    extraire_et_envoyer()