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
        st.title("🛒 Marketplace")
        st.info(f"Bienvenue, {st.session_state.pseudo} !")
        solde_user = ft.afficher_solde_actuel(supabase, st.session_state.id_user)
        effectif = ft.afficher_effectif(supabase, st.session_state.id_user)
        nb_joueurs = len(effectif)
        effectif = sorted(effectif, key=lambda x: x["Valeur actuelle"], reverse=True)
        joueurs_disponibles = ft.afficher_joueurs_disponibles(supabase, st.session_state.id_user)
        joueurs_achetables, joueurs_non_achetables = fs.separer_joueurs_par_disponibilite(
            joueurs_disponibles, solde_user, nb_joueurs
        )
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            date_deadline, active_time = f.find_deadline(supabase)

            if active_time:
                st.success(f"🟢 Marché ouvert jusqu’au **{date_deadline[:10]} à {date_deadline[11:16]}**")
            else:
                st.error(f"🔒 Marché fermé — prochaine ouverture le **{date_deadline[:10]} à {date_deadline[11:16]}**")

        with col2:
            st.metric(label="💰 Solde actuel", value=f"{solde_user:.2f}")

        with col3:
            st.metric(label="👥 Joueurs dans ton effectif", value=f"{nb_joueurs}/10")
        fst.barre_grise()
        st.subheader("🧑‍🤝‍🧑 Ton effectif")

        if effectif:
            fst.afficher_effectif(supabase,effectif,action_active=True)
        else:
            st.info("Aucun joueur dans ton équipe pour le moment.")

        fst.barre_grise()
        st.subheader("📋 Joueurs disponibles")
        # Affichage des joueurs achetables
        if joueurs_achetables:
            st.markdown("### ✅ Joueurs achetables")
            
            fst.afficher_tableau(supabase,joueurs_achetables, action_label="Acheter", action_active=active_time)

        fst.barre_grise()
        # Affichage des joueurs non disponibles
        if joueurs_non_achetables:
            st.markdown("### ❌ Joueurs non disponibles")
            fst.afficher_tableau(supabase,joueurs_non_achetables, action_label="Indisponible", action_active=False)


    elif menu == "Règles du jeu":
        ps.regles_du_jeu()

    elif menu == "Déconnexion":
        st.session_state.id_user = None
        st.rerun()