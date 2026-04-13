# test_db3.py
from pathlib import Path
from dotenv import load_dotenv
import os
import psycopg2

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# Test avec paramètres séparés (pas une URL)
try:
    conn = psycopg2.connect(
        host="db.eioitlkuyfjqlgeoqryp.supabase.co",
        port=5432,
        database="postgres",
        user="postgres",
        password="Callcenter202435C3",
        sslmode="require",
        connect_timeout=15
    )
    print("Connexion OK !")
    conn.close()
except psycopg2.OperationalError as e:
    print(f"Erreur détaillée : {e.pgerror}")
    print(f"Message : {str(e)}")