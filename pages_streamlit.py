import streamlit as st
import fonctions.fonctions_standard as fs
import fonctions.fonctions_tableaux as ft
import fonctions.fonctions_streamlit as fst
import fonctions.fonctions_api as f
from datetime import datetime
import pytz

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



def prochain_match(supabase):
    ROUND_LABELS = {
        35: "Play-in",
        36: "Play-in",
        37: "Playoffs Game 1",
        38: "Playoffs Game 2",
        39: "Playoffs Game 3",
        40: "Playoffs Game 4",
        41: "Playoffs Game 5",
        42: "Final 4 - Demi-finale",
        43: "Match pour la 3e place",
        44: "Finale"
    }

    st.title("📅 Prochains matchs")
    fst.barre_grise()

    paris_tz = pytz.timezone("Europe/Paris")
    now = datetime.now(paris_tz).isoformat()

    # Récupérer les matchs à venir
    matchs = supabase.table("Calendrier") \
        .select("season, round, id_equipe1, id_equipe2, date") \
        .gte("date", now) \
        .order("date", desc=False) \
        .execute()

    if not matchs.data:
        st.info("Aucun match à venir trouvé.")
        fst.barre_grise()
        return

    for match in matchs.data:
        id_eq1 = match["id_equipe1"]
        id_eq2 = match["id_equipe2"]

        # Récupérer les noms des équipes
        nom_eq1 = supabase.table("Equipe").select("nom").eq("id_equipe", id_eq1).execute().data
        nom_eq2 = supabase.table("Equipe").select("nom").eq("id_equipe", id_eq2).execute().data

        nom_eq1 = nom_eq1[0]["nom"] if nom_eq1 else id_eq1
        nom_eq2 = nom_eq2[0]["nom"] if nom_eq2 else id_eq2

        try:
            dt = datetime.fromisoformat(match["date"]).astimezone(paris_tz)
            formatted_date = dt.strftime("%A %d %B %Y à %Hh%M")
        except:
            formatted_date = match["date"][:16]

        label_round = ROUND_LABELS.get(match["round"], f"Round {match['round']}")
        st.markdown(f"""
        ### 🏀 {nom_eq1} vs {nom_eq2}
        - **{label_round}**
        - **Saison** : {match['season']} / {match['season']+1}
        - **Date** : {formatted_date}
        """)
        st.markdown("---")

    fst.barre_grise()




def marketplace(supabase) :
    st.title("🛒 Marketplace")
    fst.barre_grise()
    solde_user = ft.afficher_solde_actuel(supabase, st.session_state.id_user)
    effectif = ft.afficher_effectif(supabase, st.session_state.id_user)
    nb_joueurs = len(effectif)
    effectif = sorted(effectif, key=lambda x: x["Valeur actuelle"], reverse=True)
    joueurs_disponibles = ft.afficher_joueurs_disponibles(supabase, st.session_state.id_user)
    joueurs_achetables, joueurs_non_achetables = fs.separer_joueurs_par_disponibilite(
        joueurs_disponibles, solde_user, nb_joueurs
    )
    col0,col1,col2, col3, col4 = st.columns([1,3,1, 1, 1])
    with col0:
        st.metric(label="👤 Utilisateur", value=st.session_state.pseudo)

    with col1:
        date_deadline, active_time = f.find_deadline(supabase)

        if active_time:
            st.success(f"🟢 Marché ouvert jusqu’au **{date_deadline[:10]} à {date_deadline[11:16]}**")
        else:
            st.error(f"🔒 Marché fermé — prochaine ouverture le **{date_deadline[:10]} à {date_deadline[11:16]}**")

    with col2:
        st.metric(label="💰 Solde actuel", value=f"{solde_user:.2f}")

    with col3:
        st.metric(label="💎 Valeur de l'effectif", value=f"{sum([v['Valeur actuelle'] for v in effectif]):.2f}")

    with col4:
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

def centre_de_donnees(supabase):
    st.title("📊 Centre de données")
    fst.barre_grise()

    # Récupérer tous les contrats actifs
    contrats_res = supabase.table("Contrat") \
        .select("id_contrat, id_equipe") \
        .is_("END", None) \
        .execute()

    if not contrats_res.data:
        st.warning("Aucun contrat actif trouvé.")
        return

    
    id_equipes = [row["id_equipe"] for row in contrats_res.data]

    equipes_res = supabase.table("Equipe") \
        .select("id_equipe, nom") \
        .in_("id_equipe", id_equipes) \
        .execute()
    
    
    # 1. Récupérer les noms d'équipes
    equipes = sorted([row["nom"] for row in equipes_res.data])

    cols = st.columns([1,1,1,1])
    # 2. Interface utilisateur
    with cols[0]:
        CODETEAM = st.multiselect("🔍 Filtrer par équipe", options=equipes, key="A")

    # 3. Filtrage des équipes sélectionnées
    if CODETEAM:
        # Récupérer les ID des équipes sélectionnées
        id_equipes_filtrees = [row["id_equipe"] for row in equipes_res.data if row["nom"] in CODETEAM]

        # Filtrer les contrats
        contrats_res.data = [row for row in contrats_res.data if row["id_equipe"] in id_equipes_filtrees]

    id_contrats = [row["id_contrat"] for row in contrats_res.data]

    # 1. Récupérer toutes les lignes correspondantes
    res = supabase.table("Valeur_Actuelle") \
        .select("id_contrat, valeur, date") \
        .in_("id_contrat", id_contrats) \
        .order("date", desc=True) \
        .execute()

    # 2. Garder seulement la ligne la plus récente par id_contrat
    latest_valeurs = {}
    for row in res.data:
        idc = row["id_contrat"]
        if idc not in latest_valeurs:
            latest_valeurs[idc] = row  # Première occurrence = date la plus récente

    # 3. Trier les lignes conservées par valeur décroissante
    valeurs_triees = sorted(latest_valeurs.values(), key=lambda x: x["valeur"], reverse=True)
    id_contrats = [row["id_contrat"] for row in valeurs_triees]

    for id_contrat in id_contrats:
        try:
            fst.afficher_stats_joueurs(supabase, id_contrat)
            fst.barre_grise()
        except Exception as e:
            st.error(f"❌ Erreur pour contrat {id_contrat} : {e}")

def mon_equipe(supabase) :
    pass

def mes_actions(supabase) :
    pass