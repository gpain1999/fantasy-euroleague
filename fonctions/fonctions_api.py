from datetime import datetime
import pytz
from supabase import create_client
from euroleague_api.game_stats import GameStats
from euroleague_api.boxscore_data  import BoxScoreData
import sys
import os
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.join(os.path.dirname(__file__), '../fonctions'))

import fonctions_standard as f
from datetime import datetime
import pytz
import numpy as np

from datetime import datetime
import pytz

def get_nombre_joueurs_actifs(supabase, id_user: int) -> int:
    res = supabase.table("Possession") \
        .select("id_possession", count="exact") \
        .eq("id_user", id_user) \
        .is_("END", None) \
        .execute()

    return res.count or 0

def vendre_joueur(supabase, id_user: int, id_contrat: int):
    paris_tz = pytz.timezone("Europe/Paris")
    now = datetime.now(paris_tz).isoformat()

    # 1. Vérifier si c’est bien une période ACTIVE
    if is_active_period(supabase) == False:
        raise Exception("⛔ Vente impossible : la période de transfert est fermée.")

    # 2. Vérifier que le joueur est bien possédé actuellement
    possession_res = supabase.table("Possession") \
        .select("id_possession") \
        .eq("id_user", id_user) \
        .eq("id_contrat", id_contrat) \
        .is_("END", None) \
        .execute()

    if not possession_res.data:
        raise Exception("⛔ Tu ne possèdes pas ce joueur.")

    id_possession = possession_res.data[0]["id_possession"]

    # 3. Mettre fin à la possession (END = now)
    supabase.table("Possession") \
        .update({"END": now}) \
        .eq("id_possession", id_possession) \
        .execute()

    # 4. Récupérer la valeur actuelle du joueur (la plus récente)
    valeur_res = supabase.table("Valeur_Actuelle") \
        .select("valeur, date") \
        .eq("id_contrat", id_contrat) \
        .order("date", desc=True) \
        .limit(1) \
        .execute()

    if not valeur_res.data:
        raise Exception("❌ Aucune valeur actuelle trouvée pour ce joueur.")

    prix = valeur_res.data[0]["valeur"]

    # 5. Récupérer le solde bancaire actuel
    banque_res = supabase.table("Banque") \
        .select("solde, datetime") \
        .eq("id_user", id_user) \
        .order("datetime", desc=True) \
        .limit(1) \
        .execute()

    if not banque_res.data:
        raise Exception("❌ Impossible de récupérer le solde bancaire.")

    solde_actuel = banque_res.data[0]["solde"]
    nouveau_solde = round(solde_actuel + prix, 2)

    # 6. Ajouter le nouveau solde en Banque
    supabase.table("Banque").insert({
        "id_user": id_user,
        "datetime": now,
        "solde": nouveau_solde
    }).execute()

    # 7. Ajouter une ligne dans Transaction (type = False = vente)
    supabase.table("Transaction").insert({
        "id_user": id_user,
        "id_contrat": id_contrat,
        "type_transaction": False,  # Vente
        "datetime": now,
        "prix": prix
    }).execute()

    print(f"✅ Vente effectuée : joueur {id_contrat} vendu {prix} crédits. Nouveau solde : {nouveau_solde}")


def acheter_joueur(supabase, id_user: int, id_contrat: int):
    paris_tz = pytz.timezone("Europe/Paris")
    now = datetime.now(paris_tz).isoformat()

    # 1. Vérifier si c’est bien une période ACTIVE (donc is_active_period == True)
    if is_active_period(supabase) == False:
        raise Exception("⛔ Achat impossible : la période de transfert est actuellement fermée.")

    # 2. Vérifier si le joueur est déjà dans l’équipe (possession active)
    possession_check = supabase.table("Possession") \
        .select("id_possession") \
        .eq("id_user", id_user) \
        .eq("id_contrat", id_contrat) \
        .is_("END", None) \
        .execute()

    if possession_check.data:
        raise Exception("⛔ Ce joueur est déjà dans ton équipe.")

    # 3. Vérifier qu’il y a moins de 10 joueurs actifs dans l’équipe
    team_count = get_nombre_joueurs_actifs(supabase, id_user)

    if team_count >= 10:
        raise Exception("⛔ Tu as déjà 10 joueurs dans ton équipe.")

    # 4. Trouver la valeur actuelle du joueur (la plus récente)
    valeur_res = supabase.table("Valeur_Actuelle") \
        .select("valeur, date") \
        .eq("id_contrat", id_contrat) \
        .order("date", desc=True) \
        .limit(1) \
        .execute()

    if not valeur_res.data:
        raise Exception("❌ Aucune valeur actuelle trouvée pour ce joueur.")

    prix = valeur_res.data[0]["valeur"]

    # 5. Vérifier le solde bancaire de l'utilisateur
    banque_res = supabase.table("Banque") \
        .select("solde, datetime") \
        .eq("id_user", id_user) \
        .order("datetime", desc=True) \
        .limit(1) \
        .execute()

    if not banque_res.data:
        raise Exception("❌ Impossible de récupérer le solde bancaire.")

    solde_actuel = banque_res.data[0]["solde"]

    if solde_actuel < prix:
        raise Exception(f"⛔ Achat refusé : tu as {solde_actuel} crédits, il t’en faut {prix}.")

    # 6. Créer la Possession
    supabase.table("Possession").insert({
        "id_user": id_user,
        "id_contrat": id_contrat,
        "START": now,
        "END": None
    }).execute()

    # 7. Mettre à jour le solde dans Banque
    nouveau_solde = round(solde_actuel - prix, 2)

    supabase.table("Banque").insert({
        "id_user": id_user,
        "datetime": now,
        "solde": nouveau_solde
    }).execute()

    # 8. Ajouter une ligne dans Transaction
    supabase.table("Transaction").insert({
        "id_user": id_user,
        "id_contrat": id_contrat,
        "type_transaction": True,  # Achat
        "datetime": now,
        "prix": prix
    }).execute()

    print(f"✅ Achat effectué : joueur {id_contrat} pour {prix} crédits. Nouveau solde : {nouveau_solde}")


def is_active_period(supabase) -> bool:
    # Obtenir l'heure actuelle en timezone Paris
    paris = pytz.timezone("Europe/Paris")
    now = datetime.now(paris).isoformat()

    # Cherche une deadline active maintenant
    res = supabase.table("Deadline") \
        .select("START, END") \
        .lte("START", now) \
        .gte("END", now) \
        .execute()

    # Si une ligne correspond, on est en période INACTIVE
    if res.data:
        return False
    return True

def add_deadline(supabase, start: str, end: str):
    """
    Ajoute une période de deadline dans la table Deadline.

    Paramètres :
    - start : str → timestamp ISO 8601 (ex: '2025-01-03T00:00:00')
    - end   : str → timestamp ISO 8601 (ex: '2025-01-05T20:00:00')
    """
    result = supabase.table("Deadline").insert({
        "START": start,
        "END": end
    }).execute()

    if result.data:
        print(f"✅ Deadline ajoutée : {start} → {end}")
    else:
        print("❌ Erreur lors de l'ajout de la deadline")

def maj_valeur_actuelle(supabase,id_update):
    # Obtenir la date actuelle
    paris_tz = pytz.timezone("Europe/Paris")
    now = datetime.now(paris_tz).isoformat()

    # 1. Récupérer tous les contrats actifs + id_player dans id_update
    contrats = supabase.table("Contrat") \
        .select("id_contrat, id_joueur") \
        .is_("END", None) \
        .in_("id_joueur", id_update) \
        .execute()

    if not contrats.data:
        print("❌ Aucun contrat actif trouvé.")
        return

    for contrat in contrats.data:
        id_contrat = contrat["id_contrat"]

        # 2. Récupérer les performances liées à ce contrat
        perf_res = supabase.table("Performance") \
            .select("PER, id_match") \
            .eq("id_contrat", id_contrat) \
            .execute()

        if not perf_res.data:
            print(f"ℹ️ Aucune performance pour contrat {id_contrat}")
            continue

        # 3. Ajouter la date de chaque match
        performances = []
        for p in perf_res.data:
            match_res = supabase.table("Match") \
                .select("date") \
                .eq("id_match", p["id_match"]) \
                .execute()
            if match_res.data:
                performances.append({
                    "PER": p["PER"],
                    "date": match_res.data[0]["date"]
                })

        if len(performances) == 0:
            continue

        # 4. Trier par date décroissante et prendre les 4 derniers
        performances.sort(key=lambda x: x["date"], reverse=True)
        derniers_PER = [p["PER"] for p in performances[:4]]
        moyenne = round(max(np.mean(derniers_PER),0)*4)/4

        # 5. Insérer dans Valeur_Actuelle
        insert_res = supabase.table("Valeur_Actuelle").insert({
            "id_contrat": id_contrat,
            "valeur": moyenne,
            "date": now
        }).execute()

        if insert_res.data:
            print(f"✅ Valeur ajoutée pour contrat {id_contrat} → {moyenne}")
        else:
            print(f"❌ Échec insertion pour contrat {id_contrat}")


def ajouter_user(supabase, pseudo: str, mot_de_passe: str, adresse_mail: str = ""):
    # 0. Vérifier que l'email est valide (si fourni)
    if adresse_mail:
        regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(regex, adresse_mail):
            raise ValueError("L’adresse mail fournie n’est pas valide.")

        # Vérifier si le mail est déjà utilisé
        existing_mail_response = supabase.table("User") \
            .select("adresse_mail") \
            .eq("adresse_mail", adresse_mail) \
            .execute()

        if existing_mail_response.data:
            raise Exception("Cette adresse mail est déjà utilisée.")

    # 1. Vérifier si le pseudo est déjà utilisé
    existing_user_response = supabase.table("User") \
        .select("pseudo") \
        .eq("pseudo", pseudo) \
        .execute()

    if existing_user_response.data:
        raise Exception("Le pseudo est déjà utilisé, veuillez en choisir un autre.")

    # 2. Hasher le mot de passe
    mot_de_passe_hash = f.hash_password(mot_de_passe)

    # 3. Ajouter dans la table User
    user_response = supabase.table("User").insert({
        "pseudo": pseudo,
        "mot_de_passe": mot_de_passe_hash,
        "adresse_mail": adresse_mail
    }).execute()

    if not user_response.data:
        raise Exception("Erreur lors de l'ajout de l'utilisateur")

    # 4. Récupérer l'id_user généré
    id_user = user_response.data[0]["id_user"]

    # 5. Ajouter une entrée dans Banque
    paris_tz = pytz.timezone("Europe/Paris")
    now = datetime.now(paris_tz).isoformat()

    supabase.table("Banque").insert({
        "id_user": id_user,
        "datetime": now,
        "solde": 110.0
    }).execute()

    print(f"✅ Utilisateur {pseudo} ajouté avec id {id_user} et solde initial 110")

def ajouter_equipe(supabase, id_equipe: str, nom: str):
    # Vérifier que l'ID est bien 3 lettres
    if len(id_equipe) != 3 or not id_equipe.isalpha():
        raise ValueError("L’ID d’équipe doit être 3 lettres")

    id_equipe = id_equipe.upper()

    # 1. Vérifier si l'équipe existe déjà
    res = supabase.table("Equipe") \
        .select("id_equipe") \
        .eq("id_equipe", id_equipe) \
        .execute()

    if res.data:
        print(f"ℹ️ Équipe {id_equipe} existe déjà, aucune modification.")
        return

    # 2. Insérer la nouvelle équipe
    result = supabase.table("Equipe").insert({
        "id_equipe": id_equipe,
        "nom": nom
    }).execute()

    if result.data:
        print(f"✅ Équipe {id_equipe} - {nom} ajoutée.")
    else:
        print("❌ Échec de l’ajout de l’équipe.")


def ajouter_joueur(supabase,id_joueur: str, nom: str, prenom: str):
    # Supprime le joueur existant s'il existe (optionnel, selon ta logique)
    supabase.table("Joueur").delete().eq("id_joueur", id_joueur).execute()

    # Ajoute un nouveau joueur
    result = supabase.table("Joueur").insert({
        "id_joueur": id_joueur,
        "nom": nom,
        "prenom": prenom
    }).execute()

    if result.data:
        print(f"✅ Joueur ajouté : {prenom} {nom} (ID {id_joueur})")
    else:
        print("❌ Échec de l’ajout du joueur.")

def ajouter_joueur_si_absent(supabase, id_joueur: str, nom: str, prenom: str):
    # Vérifie si le joueur existe déjà dans la table
    res = supabase.table("Joueur") \
        .select("id_joueur") \
        .eq("id_joueur", id_joueur) \
        .execute()

    if not res.data:
        ajouter_joueur(supabase, id_joueur, nom, prenom)
    else:
        print(f"ℹ️ Joueur déjà existant : {prenom.title()} {nom.upper()}")

def ajouter_contrat(supabase, id_joueur: str, id_equipe: str, date_debut: str = None):
    # 1. Gérer la date de début
    if date_debut:
        start = date_debut  # doit être déjà formatée ISO (ex: "2025-05-01T12:00:00")
    else:
        paris_tz = pytz.timezone("Europe/Paris")
        start = datetime.now(paris_tz).isoformat()

    # 2. Clôturer le contrat actif s’il existe
    res = supabase.table("Contrat") \
        .select("id_contrat") \
        .eq("id_joueur", id_joueur) \
        .is_("END", None) \
        .execute()

    if res.data:
        id_contrat_actuel = res.data[0]["id_contrat"]
        supabase.table("Contrat") \
            .update({"END": start}) \
            .eq("id_contrat", id_contrat_actuel) \
            .execute()
        print(f"⏹ Contrat {id_contrat_actuel} terminé à {start}")

    # 3. Créer le nouveau contrat
    result = supabase.table("Contrat").insert({
        "id_joueur": id_joueur,
        "id_equipe": id_equipe.upper(),
        "START": start,
        "END": None
    }).execute()

    if result.data:
        id_new = result.data[0]["id_contrat"]
        print(f"✅ Nouveau contrat {id_new} pour joueur {id_joueur} → {id_equipe} (début : {start})")
    else:
        print("❌ Échec de l’ajout du contrat.")

def finir_contrats_equipe(supabase, id_equipe: str):
    id_equipe = id_equipe.upper()

    # Récupérer tous les contrats actifs (END = NULL) de cette équipe
    contrats = supabase.table("Contrat") \
        .select("id_joueur") \
        .eq("id_equipe", id_equipe) \
        .is_("END", None) \
        .execute()

    if not contrats.data:
        print(f"ℹ️ Aucun contrat actif trouvé pour l’équipe {id_equipe}.")
        return

    # Boucle sur tous les joueurs concernés
    for contrat in contrats.data:
        id_joueur = contrat["id_joueur"]
        try:
            finir_contrat(supabase, id_joueur, id_equipe)
        except Exception as e:
            print(f"⚠️ Erreur sur {id_joueur} ({id_equipe}) : {e}")

    print(f"✅ Tous les contrats actifs de l’équipe {id_equipe} ont été clôturés.")

def finir_contrat(supabase, id_joueur: str, id_equipe: str):
    id_equipe = id_equipe.upper()
    paris_tz = pytz.timezone("Europe/Paris")
    now = datetime.now(paris_tz).isoformat()

    # Rechercher le contrat actif (END IS NULL)
    res = supabase.table("Contrat") \
        .select("id_contrat") \
        .eq("id_joueur", id_joueur) \
        .eq("id_equipe", id_equipe) \
        .is_("END", None) \
        .execute()

    if res.data:
        id_contrat = res.data[0]["id_contrat"]

        # 1. Clôturer le contrat dans Contrat
        supabase.table("Contrat") \
            .update({"END": now}) \
            .eq("id_contrat", id_contrat) \
            .execute()
        print(f"✅ Contrat {id_contrat} terminé pour joueur {id_joueur} avec {id_equipe} à {now}")

        # 2. Chercher les utilisateurs possédant ce contrat encore actif
        possessions = supabase.table("Possession") \
            .select("id_user") \
            .eq("id_contrat", id_contrat) \
            .is_("END", None) \
            .execute()

        if possessions.data:
            for poss in possessions.data:
                id_user = poss["id_user"]
                try:
                    vendre_joueur(supabase, id_user, id_contrat)
                except Exception as e:
                    print(f"⚠️ Erreur lors de la vente auto pour user {id_user} : {e}")
        else:
            print("ℹ️ Aucun utilisateur ne possédait ce joueur.")
    else:
        print(f"ℹ️ Aucun contrat actif trouvé pour joueur {id_joueur} et équipe {id_equipe}")



def verifier_ou_ajouter_contrat(supabase, id_joueur: str, id_equipe: str, date_debut: str = None):
    id_equipe = id_equipe.upper()

    # Rechercher un contrat actif pour ce joueur et cette équipe
    res = supabase.table("Contrat") \
        .select("id_contrat") \
        .eq("id_joueur", id_joueur) \
        .eq("id_equipe", id_equipe) \
        .is_("END", None) \
        .execute()

    if not res.data:
        ajouter_contrat(supabase, id_joueur, id_equipe, date_debut)
    else:
        print(f"ℹ️ Contrat actif déjà en place pour {id_joueur} → {id_equipe}")


def ajouter_match(supabase, game_code: int, season: int,round : int, id_equipe_1: str, id_equipe_2: str, 
                  score_1: int, score_2: int, date_match: str = None):
    id_equipe_1 = id_equipe_1.upper()
    id_equipe_2 = id_equipe_2.upper()

    if id_equipe_1 == id_equipe_2:
        raise ValueError("Les deux équipes doivent être différentes.")

    # Vérifie si le match existe déjà
    res = supabase.table("Match") \
        .select("id_match") \
        .eq("id_match", game_code) \
        .eq("season", season) \
        .eq("round", round) \
        .execute()


    if res.data:
        print(f"ℹ️ Match déjà existant : saison {season}, match {game_code}")
        return

    # Date par défaut = maintenant
    if not date_match:
        paris_tz = pytz.timezone("Europe/Paris")
        date_match = datetime.now(paris_tz).isoformat()

    # Insertion
    result = supabase.table("Match").insert({
        "id_match": game_code,
        "season": season,
        "id_equipe_1": id_equipe_1,
        "id_equipe_2": id_equipe_2,
        "score_1": score_1,
        "score_2": score_2,
        "date": date_match
    }).execute()

    if result.data:
        print(f"✅ Match ajouté : {id_equipe_1} {score_1} - {score_2} {id_equipe_2}")
    else:
        print("❌ Échec de l’ajout du match.")


def ajouter_performance(supabase, season: int, id_match: int, id_contrat: int, per: int, date: str = None):
    # 0. Date = maintenant (heure de Paris) si non fournie
    if not date:
        paris_tz = pytz.timezone("Europe/Paris")
        date = datetime.now(paris_tz).isoformat()

    # 1. Corriger un PER négatif
    if per < 0:
        print(f"⚠️ PER négatif détecté pour contrat {id_contrat}, ajusté à 0.")
        per = 0

    # 2. Ajouter la performance
    insert_res = supabase.table("Performance").insert({
        "season": season,
        "id_match": id_match,
        "id_contrat": id_contrat,
        "PER": per
    }).execute()

    if not insert_res.data:
        raise Exception("❌ Échec de l’ajout de la performance.")

    id_performance = insert_res.data[0]["id_performance"]
    print(f"✅ Performance ajoutée : id {id_performance}, contrat {id_contrat}, PER = {per}")

    # 3. Trouver les utilisateurs qui possédaient ce joueur à ce moment-là
    possession_res = supabase.table("Possession") \
        .select("id_user") \
        .eq("id_contrat", id_contrat) \
        .lte("START", date) \
        .or_(f"END.gte.{date},END.is.null") \
        .execute()

    if not possession_res.data:
        print("ℹ️ Aucun utilisateur ne possédait ce joueur à cette date.")
        return id_performance

    # 4. Insérer dans Perf_User
    for row in possession_res.data:
        id_user = row["id_user"]
        supabase.table("Perf_User").insert({
            "id_performance": id_performance,
            "id_user": id_user
        }).execute()
        print(f"➕ Ajout de la performance {id_performance} pour user {id_user} dans Perf_User")

    return id_performance

def recuperer_id_contrat(supabase, id_joueur: str, id_equipe: str) -> int | None:
    id_equipe = id_equipe.upper()

    res = supabase.table("Contrat") \
        .select("id_contrat") \
        .eq("id_joueur", id_joueur) \
        .eq("id_equipe", id_equipe) \
        .is_("END", None) \
        .execute()

    if res.data:
        return res.data[0]["id_contrat"]
    else:
        print(f"ℹ️ Aucun contrat actif trouvé pour {id_joueur} dans l’équipe {id_equipe}")
        return None
    

def get_match_ids_par_saison(supabase, saison: int = 2024):
    res = supabase.table("Match") \
        .select("id_match") \
        .eq("season", saison) \
        .execute()

    if res.data:
        return [match["id_match"] for match in res.data]
    else:
        print(f"ℹ️ Aucun match trouvé pour la saison {saison}")
        return []

def ajouter_match_calendrier(supabase, id_match: int, season: int, round_: int,
                             id_equipe1: str, id_equipe2: str, date_str: str = None):
    # Vérifier que les deux équipes sont différentes
    if id_equipe1.upper() == id_equipe2.upper():
        raise ValueError("Les deux équipes doivent être différentes.")

    # Formatage des ID
    id_equipe1 = id_equipe1.upper()
    id_equipe2 = id_equipe2.upper()

    # Date par défaut = maintenant (heure de Paris)
    if not date_str:
        paris = pytz.timezone("Europe/Paris")
        date_str = datetime.now(paris).isoformat()

    # 🔍 Vérification d'existence
    existing = supabase.table("Calendrier") \
        .select("id_match") \
        .eq("id_match", id_match) \
        .eq("season", season) \
        .eq("round", round_) \
        .execute()

    if existing.data:
        # 🔄 Supprimer l'existant
        supabase.table("Calendrier") \
            .delete() \
            .eq("id_match", id_match) \
            .eq("season", season) \
            .eq("round", round_) \
            .execute()
        print(f"🔁 Ancien match supprimé pour id_match={id_match}, round={round_}")

    # ✅ Insertion
    result = supabase.table("Calendrier").insert({
        "id_match": id_match,
        "season": season,
        "round": round_,
        "id_equipe1": id_equipe1,
        "id_equipe2": id_equipe2,
        "date": date_str
    }).execute()

    if result.data:
        print(f"✅ Match ajouté au calendrier : {id_equipe1} vs {id_equipe2} (Round {round_})")
    else:
        print("❌ Échec de l’ajout au calendrier.")

def nettoyer_calendrier(supabase):
    # 1. Récupérer tous les triplets (id_match, season, round) de Match
    matchs = supabase.table("Match") \
        .select("id_match, season, round") \
        .execute()

    if not matchs.data:
        print("❌ Aucun match trouvé dans Match.")
        return

    # 2. Pour chaque triplet, supprimer s’il existe dans Calendrier
    for match in matchs.data:
        id_match = match["id_match"]
        season = match["season"]
        round_ = match["round"]

        # Supprimer dans Calendrier si le même triplet existe
        supabase.table("Calendrier") \
            .delete() \
            .eq("id_match", id_match) \
            .eq("season", season) \
            .eq("round", round_) \
            .execute()

    print("✅ Calendrier nettoyé : doublons supprimés par correspondance avec Match.")

def get_update_match_data(supabase, season):
    """
    Récupère les données de match à mettre à jour.
    """
    bs = BoxScoreData()
    gs = GameStats()

    # 🔹 Récupération des matchs déjà présents dans la base de données
    match_ids_season = get_match_ids_par_saison(supabase, season)
    
    # 🔹 Récupération des matchs non présents dans la base de données
    not_yet = list(set([i for i in range(1,334)]) - set(match_ids_season))
    

    match_ids_season = get_match_ids_par_saison(supabase, season)
    not_yet = list(set([i for i in range(1,334)]) - set(match_ids_season))
    id_update = []
    for game_code in not_yet:
        print(f"\n🔄 Traitement du match {game_code}...")
        try:
            # 🔹 Récupération des données du match
            ggs = gs.get_game_report(season=season, game_code=game_code)
            # 🔹 Équipes
            id_equipe_local = ggs['local.club.code'].to_list()[0]
            nom_local = ggs['local.club.name'].to_list()[0]
            id_equipe_road = ggs['road.club.code'].to_list()[0]
            nom_road = ggs['road.club.name'].to_list()[0]
            round = ggs['Round'].to_list()[0]
            score_local = ggs['local.score'].to_list()[0]
            score_road = ggs['road.score'].to_list()[0]
            date = ggs["date"].to_list()[0]

            if score_local == 0 and score_road == 0:
                ajouter_match_calendrier(
                                supabase,
                                id_match=game_code,
                                season=season,
                                round_=round,
                                id_equipe1=id_equipe_local,
                                id_equipe2=id_equipe_road,
                                date_str=date
                            )
                print(f"⚠️ Match {game_code} non joué, pas de données disponibles.")
                continue

            boxscore = bs.get_player_boxscore_stats_data(season=season, gamecode=game_code)
            
            # 🔹 Formatage de la date
            
            
            # 🔹 Nettoyage du boxscore
            boxscore = boxscore[
                (boxscore['Minutes'] != "DNP") &
                (boxscore["Player_ID"] != "Team") &
                (boxscore["Player_ID"] != "Total")
            ][["Player_ID", "Player", "Team", "Valuation"]].reset_index(drop=True)

            id_update = list(set(boxscore["Player_ID"].to_list() + id_update))



            # 🔹 Ajout des équipes
            ajouter_equipe(supabase, id_equipe_local, nom_local)
            ajouter_equipe(supabase, id_equipe_road, nom_road)

            # 🔹 Ajout du match
            if round :
                ajouter_match(
                    supabase, game_code, season,round,
                    id_equipe_local, id_equipe_road,
                    score_local,
                    score_road,
                    date
                )

            # 🔹 Traitement de chaque joueur
            for _, row in boxscore.iterrows():
                id_joueur = row["Player_ID"]
                equipe = row["Team"]
                try:
                    nom, prenom = row["Player"].split(", ")
                except ValueError:
                    print(f"❌ Format incorrect pour Player : {row['Player']} → ignoré")
                    continue

                perf = row["Valuation"]

                try:
                    ajouter_joueur_si_absent(supabase, id_joueur, nom, prenom)
                    verifier_ou_ajouter_contrat(supabase, id_joueur, equipe, date)
                    id_contrat = recuperer_id_contrat(supabase, id_joueur, equipe)
                    if id_contrat:
                        ajouter_performance(supabase, season, game_code, id_contrat, perf,date)
                    else:
                        print(f"⚠️ Aucun contrat actif pour {id_joueur} → {equipe}")
                except Exception as e:
                    print(f"❌ Erreur pour le joueur {id_joueur} ({nom} {prenom}) : {e}")
                    continue
            ok_one_time = True
        except Exception as e:
            print(f"\n❌ Erreur dans game_code {game_code} → {e}")
            continue
    if id_update:
        maj_valeur_actuelle(supabase,id_update)
    
    nettoyer_calendrier(supabase)
