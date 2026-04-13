"""
Reconciliation script for call center pipeline.
Validates data consistency between sources.
"""
import sys
import uuid
from datetime import datetime, timezone, timedelta
from utils.api_client import fetch_all_calls, fetch_api_count
from utils.transformations import build_row, filter_calls
from utils.db import insert_call, get_db_count, save_audit

def run():
    run_id  = str(uuid.uuid4())
    now     = datetime.now(timezone.utc)
    from_dt = (now - timedelta(hours=24)).isoformat()
    to_dt   = now.isoformat()

    print(f"[{run_id}] Réconciliation : {from_dt} → {to_dt}")

    try:
        api_count = fetch_api_count(from_dt, to_dt)
        db_count  = get_db_count(from_dt, to_dt)
        gap       = api_count - db_count

        print(f"API: {api_count} | DB: {db_count} | Gap: {gap}")

        inserted = 0
        ignored  = 0

        if gap > 0:
            print(f"{gap} appels manquants → re-fetch...")
            raw_calls   = fetch_all_calls(from_dt, to_dt)
            valid_calls = filter_calls(raw_calls)

            for c in valid_calls:
                vars_dict = c.get("variables", {})
                from_num  = c.get("from_number", "")
                unique_id = c.get("unique_id") or str(uuid.uuid4())
                row       = build_row(c, vars_dict, unique_id, from_num)

                if insert_call(row):
                    inserted += 1
                else:
                    ignored += 1

            print(f"Réconciliation → Insérés: {inserted} | Ignorés: {ignored}")

            save_audit(
                run_id, "reconciliation", from_dt, to_dt,
                api_declared=api_count,
                api_fetched=len(raw_calls),
                after_filter=len(valid_calls),
                inserted=inserted,
                ignored=ignored
            )
        else:
            print("Aucun gap. Rien à faire.")
            save_audit(run_id, "reconciliation", from_dt, to_dt,
                       api_declared=api_count, inserted=0, ignored=0)

    except Exception as e:
        print(f"ERREUR: {e}")
        save_audit(run_id, "reconciliation", from_dt, to_dt, error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    run()