import fonctions_standard as fs
import streamlit as st
import fonctions_tableaux as ft
import fonctions_api as f
from datetime import datetime, timedelta
import pytz

def barre_grise() :
    st.markdown(
    f'''
    <p style="font-size:{int(27)}px; text-align: center; background-color: grey;color: black; padding: 3px; border-radius: 5px;">
        <b></b>
    </p>
    ''',
    unsafe_allow_html=True
    )

def afficher_effectif(supabase, effectif, action_active=True):
    if not effectif:
        return

    if action_active:
        if st.button("💸 Vendre toute l'équipe"):
            for joueur in effectif:
                f.vendre_joueur(supabase, st.session_state.id_user, joueur["id_contrat"])
            st.rerun()

    # En-têtes
    cols = st.columns([2, 2, 2, 2, 2, 2, 2,2, 1])
    cols[0].markdown("**Joueur**")
    cols[1].markdown("**Équipe**")
    cols[2].markdown("**Valeur actuelle**")
    cols[3].markdown("**Date d’achat**")
    cols[4].markdown("**Prix d’achat**")
    cols[5].markdown("**Dernier match**")
    cols[6].markdown("**Dernier PER**")
    cols[7].markdown("**PER N-4**")
    cols[8].markdown("**Action**")

    for joueur in effectif:
        cols = st.columns([2, 2, 2, 2, 2, 2, 2,2, 1])
        cols[0].markdown(joueur["Joueur"])
        cols[1].markdown(joueur["Équipe"])
        cols[2].markdown(str(joueur["Valeur actuelle"]))
        cols[3].markdown(f"{str(joueur['Date d’achat'])[:10]} {str(joueur['Date d’achat'])[11:16]}")
        cols[4].markdown(str(joueur["Prix d’achat"]))
        cols[5].markdown(str(joueur["Dernier match"])[:10])
        cols[6].markdown(str(joueur["Dernier PER"]))
        cols[7].markdown(str(joueur["PER_4"]))

        if action_active:
            if cols[8].button("Vendre", key=f"vendre_{joueur['id_contrat']}"):
                f.vendre_joueur(supabase, st.session_state.id_user, joueur["id_contrat"])
                st.rerun()
        else:
            cols[8].button("🚫", key=f"desactiver_{joueur['id_contrat']}", disabled=True)


def afficher_tableau(supabase,joueurs, action_label="Acheter", action_active=True):
    if not joueurs:
        return
    
    # Récupération des équipes disponibles dans les joueurs
    equipes = sorted(list({j["Équipe"] for j in joueurs}))
    cols = st.columns([1,1,1,1])
    with cols[0]:
        CODETEAM = st.multiselect("🔍 Filtrer par équipe", options=equipes,key="A" + action_label)
        if CODETEAM:
            joueurs = [j for j in joueurs if j["Équipe"] in CODETEAM]

    with cols[1]:
        filtre_moins_1_mois = st.checkbox("📅 Dernier Match < 1 mois",key="B"+action_label)

        if filtre_moins_1_mois:
            paris_tz = pytz.timezone("Europe/Paris")
            now = datetime.now(paris_tz)

            joueurs_filtrés = []
            for j in joueurs:
                date_str = j.get("Dernier match")
                if not date_str:
                    continue
                try:
                    match_dt = datetime.fromisoformat(date_str).astimezone(paris_tz)
                    if match_dt >= now - timedelta(days=30):
                        joueurs_filtrés.append(j)
                except:
                    continue

            joueurs = joueurs_filtrés

        filtre_val_sup_per4 = st.checkbox("📊 Valeur > PER N-4",key="C" + action_label)
        if filtre_val_sup_per4:
            joueurs = [
                j for j in joueurs
                if isinstance(j["Valeur actuelle"], (int, float)) and isinstance(j["PER_4"], (int, float))
                and j["Valeur actuelle"] > j["PER_4"]
            ]

    # En-têtes
    cols = st.columns([2, 2, 2, 2, 2,2, 1])
    cols[0].markdown("**Joueur**")
    cols[1].markdown("**Équipe**")
    cols[2].markdown("**Valeur**")
    cols[3].markdown("**Dernier match**")
    cols[4].markdown("**Dernier PER**")
    cols[5].markdown("**PER N-4**")
    cols[6].markdown("**Action**")

    for joueur in joueurs:
        cols = st.columns([2, 2, 2, 2, 2,2, 1])
        cols[0].markdown(str(joueur["Joueur"]))
        cols[1].markdown(str(joueur["Équipe"]))
        cols[2].markdown(str(f"{joueur['Valeur actuelle']:.2f}"))
        cols[3].markdown(str(joueur["Dernier match"])[:10])
        cols[4].markdown(str(joueur["Dernier PER"]))
        cols[5].markdown(str(joueur["PER_4"]))
        if action_active:
            if cols[6].button(action_label, key=f"acheter_{joueur['id_contrat']}"):
                try:
                    f.acheter_joueur(supabase, st.session_state.id_user, joueur["id_contrat"])
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        else:
            cols[6].button("🚫", key=f"desactiver_{joueur['id_contrat']}", disabled=True)
