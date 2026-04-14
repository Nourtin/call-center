"""
diagnostic.py — Lance ce fichier EN PREMIER pour identifier les erreurs
"""
import os, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
CALL_API_BASE = os.environ.get("CALL_API_BASE_URL", "")
CALL_API_TOKEN = os.environ.get("CALL_API_TOKEN", "")

print("=" * 55)
print("DIAGNOSTIC — Connexions")
print("=" * 55)

# ── 1) Vérif variables .env ────────────────────────────────
print("\n1) Variables .env :")
print(f"   SUPABASE_URL   : {'✅ ' + SUPABASE_URL if SUPABASE_URL else '❌ manquante'}")
print(f"   SUPABASE_KEY   : {'✅ ' + SUPABASE_KEY[:20] + '...' if SUPABASE_KEY else '❌ manquante'}")
print(f"   CALL_API_BASE  : {'✅ ' + CALL_API_BASE if CALL_API_BASE else '❌ manquante'}")
print(f"   CALL_API_TOKEN : {'✅ ' + CALL_API_TOKEN[:10] + '...' if CALL_API_TOKEN else '❌ manquante'}")

# ── 2) Alerte clé publishable ──────────────────────────────
if SUPABASE_KEY.startswith("sb_publishable_"):
    print("\n⚠️  PROBLÈME DÉTECTÉ : SUPABASE_KEY commence par 'sb_publishable_'")
    print("   Cette clé ne fonctionne PAS avec l'API REST Supabase.")
    print("   ➜ Va dans : Supabase Dashboard > Settings > API")
    print("   ➜ Copie la clé 'anon public' (commence par 'eyJ...')")
    print("   ➜ Mets-la dans .env : SUPABASE_KEY=eyJ...")

# ── 3) Test Supabase REST ──────────────────────────────────
print("\n2) Test Supabase REST API :")
tables_to_try = ["appels", "pipeline_audit", "appels_backup"]
for table in tables_to_try:
    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
            params={"select": "*", "limit": 1},
            timeout=10,
        )
        if r.status_code == 200:
            print(f"   ✅ Table '{table}' : accessible")
        elif r.status_code == 401:
            print(f"   ❌ Table '{table}' : 401 UNAUTHORIZED — clé invalide")
            break
        elif r.status_code == 404:
            print(f"   ⚠️  Table '{table}' : introuvable (404)")
        else:
            print(f"   ❌ Table '{table}' : {r.status_code} → {r.text[:100]}")
    except Exception as e:
        print(f"   ❌ Erreur réseau : {e}")

# ── 4) Test API Calls ──────────────────────────────────────
print("\n3) Test API CallRounded :")
for header_format in [
    {"X-API-Key": CALL_API_TOKEN},
    {"Authorization": f"Bearer {CALL_API_TOKEN}"},
]:
    try:
        r = requests.get(
            f"{CALL_API_BASE}/calls",
            headers=header_format,
            params={"page": 1, "per_page": 1},
            timeout=15,
        )
        key_name = list(header_format.keys())[0]
        if r.status_code == 200:
            print(f"   ✅ {key_name} : fonctionne (200)")
        elif r.status_code == 401:
            print(f"   ❌ {key_name} : refusé (401)")
        else:
            print(f"   ⚠️  {key_name} : {r.status_code}")
    except Exception as e:
        print(f"   ❌ {key_name} : erreur réseau → {e}")
# colle ça dans un fichier check_columns.py et lance-le
import os, requests
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

r = requests.get(
    f"{os.environ['SUPABASE_URL']}/rest/v1/appels",
    headers={"apikey": os.environ["SUPABASE_KEY"], "Authorization": f"Bearer {os.environ['SUPABASE_KEY']}"},
    params={"select": "*", "limit": 1},
    timeout=10,
)
import json
print(json.dumps(r.json(), indent=2, ensure_ascii=False))

print("\n" + "=" * 55)
print("FIN DU DIAGNOSTIC")
print("=" * 55)
print("\n📌 Action requise si SUPABASE_KEY est invalide :")
print("   1. Ouvre https://supabase.com → ton projet")
print("   2. Settings → API → 'anon public' ou 'service_role'")
print("   3. Remplace SUPABASE_KEY dans ton fichier .env")