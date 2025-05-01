import os
from supabase import create_client
import fonctions.fonctions_api as f

# On lit directement les variables d'environnement injectées par GitHub
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
season = os.getenv("SEASON")

supabase = create_client(url, key)
f.get_update_match_data(supabase, season)
