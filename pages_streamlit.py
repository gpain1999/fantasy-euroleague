import streamlit as st
import fonctions.fonctions_standard as fs
import fonctions.fonctions_tableaux as ft
import fonctions.fonctions_streamlit as fst
import fonctions.fonctions_api as f

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

def marketplace(supabase) :
    st.title("🛒 Marketplace")
    solde_user = ft.afficher_solde_actuel(supabase, st.session_state.id_user)
    effectif = ft.afficher_effectif(supabase, st.session_state.id_user)
    nb_joueurs = len(effectif)
    effectif = sorted(effectif, key=lambda x: x["Valeur actuelle"], reverse=True)
    joueurs_disponibles = ft.afficher_joueurs_disponibles(supabase, st.session_state.id_user)
    joueurs_achetables, joueurs_non_achetables = fs.separer_joueurs_par_disponibilite(
        joueurs_disponibles, solde_user, nb_joueurs
    )
    col0,col1, col2, col3 = st.columns([1,3, 1, 1])
    with col0:
        st.metric(label="Utilisateur", value=st.session_state.pseudo)
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
        fst.afficher_effectif(supabase,effectif,action_active=active_time)
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
