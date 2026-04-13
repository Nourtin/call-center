"""
Data ingestion script for call center pipeline.
Fetches data from external APIs and loads into database.
"""
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta
from utils.api_client import fetch_all_calls, fetch_api_count
from utils.transformations import build_row, filter_calls
from utils.db import insert_call, save_audit
from dotenv import load_dotenv
from utils.api_client import fetch_all_calls, fetch_api_count
from utils.transformations import build_row, filter_calls
from utils.db import insert_call, save_audit
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
def run():
    run_id  = str(uuid.uuid4())
    now     = datetime.now(timezone.utc)
    from_dt = (now - timedelta(minutes=35)).isoformat()
    to_dt   = now.isoformat()

    print(f"[{run_id}] Ingestion en cours...")

    try:
        raw_calls   = fetch_all_calls()
        valid_calls = filter_calls(raw_calls)

        inserted = 0
        ignored  = 0

        for c in valid_calls:
            vars_dict = c.get("variable_values") or {}
            from_num  = c.get("from_number", "")
            unique_id = c.get("id", str(uuid.uuid4()))  # CallRounded utilise "id"
            row       = build_row(c, vars_dict, unique_id, from_num)

            if insert_call(row):
                inserted += 1
            else:
                ignored += 1

        print(f"Terminé → Insérés: {inserted} | Ignorés: {ignored}")

    except Exception as e:
        print(f"ERREUR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()