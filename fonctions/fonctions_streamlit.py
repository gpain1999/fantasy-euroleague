import fonctions_standard as fs
import streamlit as st
import fonctions_tableaux as ft
import fonctions_api as f
from datetime import datetime, timedelta
import pytz
import numpy as np
import plotly.graph_objects as go

def barre_grise() :
    st.markdown(
    f'''
    <p style="font-size:{int(27)}px; text-align: center; background-color: grey;color: black; padding: 3px; border-radius: 5px;">
        <b></b>
    </p>
    ''',
    unsafe_allow_html=True
    )

def deconnecter() :
    st.session_state.id_user = None
    st.session_state.pseudo = None
    st.rerun()

def afficher_effectif(supabase, effectif, action_active=True):
    if not effectif:
        return

    if action_active:
        if st.button("💸 Vendre toute l'équipe"):
            for joueur in effectif:
                f.vendre_joueur(supabase, st.session_state.id_user, joueur["id_contrat"])
            st.rerun()

    # En-têtes
    cols = st.columns([2.5, 2.5, 2, 2, 2, 2, 2,2, 2,2])
    cols[0].markdown("**Joueur**")
    cols[1].markdown("**Équipe**")
    cols[2].markdown("**Date d’achat**")
    cols[3].markdown("**Prix d’achat**")
    cols[4].markdown("**Dernier match**")
    cols[5].markdown("**Dernier PER**")
    cols[6].markdown("**PER N-4**")
    cols[7].markdown("**Prix actuel**")
    cols[8].markdown("**Action**")
    cols[9].markdown("**Infos**")

    for joueur in effectif:
        cols = st.columns([2.5, 2.5, 2, 2, 2, 2, 2,2, 2,2])
        cols[0].markdown(joueur["Joueur"])
        cols[1].markdown(joueur["Équipe"])
        cols[2].markdown(f"{str(joueur['Date d’achat'])[:10]} {str(joueur['Date d’achat'])[11:16]}")
        cols[3].markdown(str(joueur["Prix d’achat"]))
        cols[4].markdown(str(joueur["Dernier match"])[:10])
        cols[5].markdown(str(joueur["Dernier PER"]))
        cols[6].markdown(str(joueur["PER_4"]))
        cols[7].markdown(str(joueur["Valeur actuelle"]))

        if action_active:
            if cols[8].button(f"Vendre", key=f"vendre_{joueur['id_contrat']}"):
                f.vendre_joueur(supabase, st.session_state.id_user, joueur["id_contrat"])
                st.rerun()
        else:
            cols[8].button("🚫", key=f"desactiver_{joueur['id_contrat']}", disabled=True)

        if cols[9].button(f"🔍 Détail", key=f"detail_{joueur['id_contrat']}"):
            st.session_state["joueur_detail"] = joueur["id_contrat"]
    
    id_detail = st.session_state.get("joueur_detail")
    if id_detail:
        joueur_detail = next((j for j in effectif if j["id_contrat"] == id_detail), None)
        if joueur_detail:
            with st.container():
                st.markdown("---")
                st.markdown(f"### 📊 Détail : {joueur_detail['Joueur']} ({joueur_detail['Équipe']})")

                # 👉 Appel de ta fonction personnalisée pour afficher les stats
                afficher_stats_joueurs(supabase, id_detail)

                # Bouton pour fermer la vue
                if st.button("Fermer", key="close_detail"):
                    del st.session_state["joueur_detail"]
                    st.rerun()

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
    cols[2].markdown("**Dernier match**")
    cols[3].markdown("**Dernier PER**")
    cols[4].markdown("**PER N-4**")
    cols[5].markdown("**Prix actuel**")
    cols[6].markdown("**Action**")

    for joueur in joueurs:
        cols = st.columns([2, 2, 2, 2, 2,2, 1])
        cols[0].markdown(str(joueur["Joueur"]))
        cols[1].markdown(str(joueur["Équipe"]))
        cols[2].markdown(str(joueur["Dernier match"])[:10])
        cols[3].markdown(str(joueur["Dernier PER"]))
        cols[4].markdown(str(joueur["PER_4"]))
        cols[5].markdown(str(f"{joueur['Valeur actuelle']:.2f}"))

        if action_active:
            if cols[6].button(action_label, key=f"acheter_{joueur['id_contrat']}"):
                try:
                    f.acheter_joueur(supabase, st.session_state.id_user, joueur["id_contrat"])
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        else:
            cols[6].button("🚫", key=f"desactiver_{joueur['id_contrat']}", disabled=True)

def afficher_stats_joueurs(supabase,id_contrat) :
    joueur_info, joueur_stat = ft.recuperations_statistiques(supabase, id_contrat)
    PER_REVERSED = list(reversed(joueur_stat["PER"]))
    DATE_REVERSED = list(reversed(joueur_stat["Date"]))
    moy_gli = fs.moyenne_glissante_4(PER_REVERSED)

    if joueur_info and joueur_stat:
        cols = st.columns([0.2,0.3,0.5])
        with cols[0]:
            st.subheader(f"🧑‍🤝‍🧑 {joueur_info['prenom']} {joueur_info['nom']}")

            st.markdown(
                f'<p style="font-size:20px;"><strong>{joueur_info["nom_equipe"]}</strong></p>',
                unsafe_allow_html=True
            )

            st.markdown(
                f'<p style="font-size:30px;">Valeur : <strong>{round(np.mean(joueur_stat["PER"][:4]), 2)}</strong></p>',
                unsafe_allow_html=True
            )

            st.markdown(
                f'<p style="font-size:20px;">Min : <strong>{round(min(moy_gli), 2)}</strong></p>',
                unsafe_allow_html=True
            )
            st.markdown(
                f'<p style="font-size:20px;">Max : <strong>{round(max(moy_gli), 2)}</strong></p>',
                unsafe_allow_html=True
            )
        with cols[1]:
                # Création du graphique avec la nouvelle courbe de moyenne glissante
            fig = go.Figure()

            for per, date in zip(PER_REVERSED, DATE_REVERSED):
                couleur = "orange" if per > 0 else "red"  # gris si 0

                # Affiche une barre visible même à 0
                fig.add_trace(go.Bar(
                    x=[date],
                    y=[per if per > 0 else 0.3],  # petite hauteur visible pour les 0
                    marker_color=couleur,
                    yaxis="y1",
                    showlegend=False
                ))


            fig.add_trace(go.Scatter(
                        x=DATE_REVERSED,
                        y=moy_gli,
                        mode="lines+markers",
                        line=dict(color='grey', width=4, dash="dot"),
                        yaxis="y1",
                        showlegend=True,
                        name=f"Evolution de la valeur de {joueur_info['prenom']} {joueur_info['nom']}"
                ))
                
            fig.update_layout(
                autosize=True,
                title = f"PER de {joueur_info['prenom']} {joueur_info['nom']}",
                xaxis_title="Date",
                yaxis_title="PER",
                legend=dict(
                    orientation="h",  # Layout horizontal
                    yanchor="top",
                    y=-0.3,  # Position sous le graphique
                    xanchor="center",
                    x=0.5  # Centré horizontalement
        ))
            
            st.plotly_chart(fig, use_container_width=True,static_plot=True)