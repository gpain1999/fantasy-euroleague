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
    menu = st.sidebar.selectbox("Menu", ["Acceuil","Mon Equipe","Marketplace","Centre de données","Les Prochains Matchs","Classement","Règles du jeu"])
    
    if st.sidebar.button("Déconnexion"):
        st.session_state.id_user = None
        st.session_state.pseudo = None
        st.rerun()

    if menu == "Acceuil":
        pass
    if menu == "Mon Equipe":
        st.title("🏀 Mon équipe")
        fst.barre_grise()
        pass

    if menu == "Marketplace":
        ps.marketplace(supabase)

    if menu == "Centre de données":
        ps.centre_de_donnees(supabase)
    
    if menu == "Les Prochains Matchs":
        ps.prochain_match(supabase)


    elif menu == "Règles du jeu":
        ps.regles_du_jeu()




