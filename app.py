import streamlit as st
from supabase import create_client
from dotenv import load_dotenv
import fonctions.fonctions_api as f
import fonctions.fonctions_tableaux as ft
import fonctions.fonctions_standard as fs
import fonctions.fonctions_streamlit as fst
import pages_streamlit as ps 
import bcrypt
import os

# Chargement des variables .env
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --------------------
# Auth helpers
# --------------------

import bcrypt




# --------------------
# UI
# --------------------
st.set_page_config(page_title="Fantasy Euroleague", page_icon="🏀", layout="wide")

if "id_user" not in st.session_state:
    st.session_state.id_user = None

# 🔐 Si l'utilisateur n'est pas connecté
if st.session_state.id_user is None:
    menu = st.sidebar.selectbox("Menu", ["Se connecter", "Créer un compte", "Règles du jeu"])

    if menu == "Se connecter":
        ps.se_connecter(supabase)

    elif menu == "Créer un compte":
        ps.creer_compte()


    elif menu == "Règles du jeu":
        ps.regles_du_jeu()



# ✅ Si connecté

else:
    menu = st.sidebar.selectbox("Menu", ["Marketplace","Règles du jeu", "Déconnexion"])

    if menu == "Marketplace":
        ps.marketplace(supabase)


    elif menu == "Règles du jeu":
        ps.regles_du_jeu()

    elif menu == "Déconnexion":
        st.session_state.id_user = None
        st.rerun()