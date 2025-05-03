import streamlit as st
import fonctions.fonctions_standard as fs

def regles_du_jeu() :
    st.title("📜 Règles du Fantasy Euroleague")

    try:
        with open("rules.txt", "r", encoding="utf-8") as f:
            rules = f.read()
        st.markdown(rules)
    except FileNotFoundError:
        st.error("Le fichier des règles (rules.txt) est introuvable.")

def creer_compte() :
    st.title("🆕 Créer un compte")
    pseudo = st.text_input("Pseudo")
    email = st.text_input("Adresse mail")
    mdp = st.text_input("Mot de passe", type="password")
    mdp_confirm = st.text_input("Confirmation mot de passe", type="password")
    if st.button("Créer mon compte"):
        fs.creer_compte(pseudo, email, mdp, mdp_confirm)

def se_connecter(supabase) :
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.title("🔐 Connexion")
        pseudo = st.text_input("Pseudo")
        mdp = st.text_input("Mot de passe", type="password")
        if st.button("Connexion"):
            id_user = fs.verifier_connexion(supabase,pseudo, mdp)
            if id_user:
                st.session_state.id_user = id_user
                st.session_state.pseudo = pseudo
                st.rerun()
            else:
                st.error("❌ Mauvais identifiants.")