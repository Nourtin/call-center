from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

print("API URL:", os.environ.get("CALL_API_BASE_URL"))
print("API TOKEN:", os.environ.get("CALL_API_TOKEN"))
print("POSTGRES:", os.environ.get("POSTGRES_CONN"))