import bcrypt
import sys
import os
import streamlit as st
import fonctions.fonctions_api as f
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def separer_joueurs_par_disponibilite(joueurs_disponibles, solde_user, nb_joueurs):
    joueurs_achetables = []
    joueurs_non_achetables = []

    for joueur in joueurs_disponibles:
        try:
            valeur = float(joueur["Valeur actuelle"])
        except:
            valeur = 0.0
        joueur["Valeur actuelle"] = valeur  # on stocke la version numérique

        if nb_joueurs >= 10 or valeur > solde_user:
            joueurs_non_achetables.append(joueur)
        else:
            joueurs_achetables.append(joueur)

    # Tri décroissant par valeur
    joueurs_achetables = sorted(joueurs_achetables, key=lambda x: x["Valeur actuelle"], reverse=True)
    joueurs_non_achetables = sorted(joueurs_non_achetables, key=lambda x: x["Valeur actuelle"], reverse=True)

    return joueurs_achetables, joueurs_non_achetables

def verifier_connexion(supabase,pseudo, mot_de_passe):
    res = supabase.table("User") \
        .select("id_user, mot_de_passe") \
        .eq("pseudo", pseudo) \
        .execute()

    if not res.data:
        return None

    user = res.data[0]
    hashed = user["mot_de_passe"]

    # Vérification du mot de passe avec bcrypt
    if bcrypt.checkpw(mot_de_passe.encode(), hashed.encode()):
        return user["id_user"]
    else:
        return None

def moyenne_glissante_4(valeurs):
    moyennes = []
    for i in range(len(valeurs)):
        fenetre = valeurs[max(0, i-3):i+1]  # de i-3 à i inclus
        moyenne = round(sum(fenetre) / len(fenetre) * 4,0)/4
        moyennes.append(moyenne)
    return moyennes

def creer_compte(supabase,pseudo, email, mdp, mdp_confirm):
    if mdp != mdp_confirm:
        st.error("❌ Les mots de passe ne correspondent pas.")
        return

    # Vérifie unicité pseudo et email
    check = supabase.table("User").select("*").or_(
        f"pseudo.eq.{pseudo},adresse_mail.eq.{email}"
    ).execute()

    if check.data:
        st.error("❌ Pseudo ou email déjà utilisé.")
        return

    f.ajouter_user(supabase, pseudo, mdp, email)