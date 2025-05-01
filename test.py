import bcrypt
import pytz
from supabase import create_client
from dotenv import load_dotenv
import os
from euroleague_api.game_stats import GameStats


import fonctions.fonctions_api as f

load_dotenv()  # charge le .env
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)



#ajouter_user(supabase,"toto", "motdepasse123", "toto@email.com")

# ajouter_equipe(supabase,"MCO", "AS Monaco")
# ajouter_equipe(supabase,"BAR", "FC Barcelone")
# ajouter_equipe(supabase,"MAD", "Real Madrid")
# ajouter_equipe(supabase,"ASV", "ASVEL")
# ajouter_equipe(supabase,"TEL", "Maccabi Tel Aviv")
# ajouter_equipe(supabase,"VIR", "Virtus Bologne")
# ajouter_equipe(supabase,"BAS", "Baskonia")
# ajouter_equipe(supabase,"BER", "Alba Berlin")
# ajouter_equipe(supabase,"IST", "Efes Istanbul")
# ajouter_equipe(supabase,"MIL", "Olimpia Milan")
# ajouter_equipe(supabase,"MUN", "Bayern Munich")
# ajouter_equipe(supabase,"OLY", "Olympiacos")
# ajouter_equipe(supabase,"PAN", "Panathinaikos")
# ajouter_equipe(supabase,"PAR", "Partizan Belgrade")
# ajouter_equipe(supabase,"PRS", "Paris Basketball")
# ajouter_equipe(supabase,"RED", "Crvena zvezda")
# ajouter_equipe(supabase,"ULK", "Fenerbahce")
# ajouter_equipe(supabase,"ZAL", "Zalgiris Kaunas")

#ajouter_joueur(supabase,"P005985", "James", "Mike")
#ajouter_contrat(supabase,"P005985", "MCO")
#f.finir_contrat(supabase,"P005985", "MCO")

# f.ajouter_joueur(supabase,"P011226", "DIALLO", "ALPHA")
# f.ajouter_contrat(supabase,"P011226", "MCO")