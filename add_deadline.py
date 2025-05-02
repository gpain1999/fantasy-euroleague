import os
from supabase import create_client
import fonctions.fonctions_api as f
from dotenv import load_dotenv

load_dotenv()  # charge le .env
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
season = os.getenv("SEASON")

supabase = create_client(url, key)

f.add_deadline(
    supabase,
    start="2025-05-02T15:00:00",
    end="2025-05-02T20:00:00"
)
