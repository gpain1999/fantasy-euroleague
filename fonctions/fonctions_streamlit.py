import fonctions_standard as fs
import streamlit as st
import fonctions_tableaux as ft
import fonctions_api as f

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
    cols = st.columns([3, 2, 2, 2, 2, 2, 2, 1])
    cols[0].markdown("**Joueur**")
    cols[1].markdown("**Équipe**")
    cols[2].markdown("**Valeur actuelle**")
    cols[3].markdown("**Date d’achat**")
    cols[4].markdown("**Prix d’achat**")
    cols[5].markdown("**Dernier match**")
    cols[6].markdown("**Dernier PER**")
    cols[7].markdown("**Action**")

    for joueur in effectif:
        cols = st.columns([3, 2, 2, 2, 2, 2, 2, 1])
        cols[0].markdown(joueur["Joueur"])
        cols[1].markdown(joueur["Équipe"])
        cols[2].markdown(str(joueur["Valeur actuelle"]))
        cols[3].markdown(f"{str(joueur['Date d’achat'])[:10]} {str(joueur['Date d’achat'])[11:16]}")
        cols[4].markdown(str(joueur["Prix d’achat"]))
        cols[5].markdown(str(joueur["Dernier match"])[:10])
        cols[6].markdown(str(joueur["Dernier PER"]))
        if action_active:
            if cols[7].button("Vendre", key=f"vendre_{joueur['id_contrat']}"):
                f.vendre_joueur(supabase, st.session_state.id_user, joueur["id_contrat"])
                st.rerun()
        else:
            cols[7].button("🚫", key=f"desactiver_{joueur['id_contrat']}", disabled=True)


def afficher_tableau(supabase,joueurs, action_label="Acheter", action_active=True):
    if not joueurs:
        return
    # En-têtes
    cols = st.columns([3, 2, 2, 2, 2, 1])
    cols[0].markdown("**Joueur**")
    cols[1].markdown("**Équipe**")
    cols[2].markdown("**Valeur**")
    cols[3].markdown("**Dernier match**")
    cols[4].markdown("**Dernier PER**")
    cols[5].markdown("**Action**")

    for joueur in joueurs:
        cols = st.columns([3, 2, 2, 2, 2, 1])
        cols[0].markdown(str(joueur["Joueur"]))
        cols[1].markdown(str(joueur["Équipe"]))
        cols[2].markdown(str(f"{joueur['Valeur actuelle']:.2f}"))
        cols[3].markdown(str(joueur["Dernier match"])[:10])
        cols[4].markdown(str(joueur["Dernier PER"]))

        if action_active:
            if cols[5].button(action_label, key=f"acheter_{joueur['id_contrat']}"):
                try:
                    f.acheter_joueur(supabase, st.session_state.id_user, joueur["id_contrat"])
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        else:
            cols[5].button("🚫", key=f"desactiver_{joueur['id_contrat']}", disabled=True)
