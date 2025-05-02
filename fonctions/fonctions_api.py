from datetime import datetime
import pytz
from supabase import create_client
from euroleague_api.game_stats import GameStats
from euroleague_api.boxscore_data  import BoxScoreData
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.join(os.path.dirname(__file__), '../fonctions'))

import fonctions_standard as f
from datetime import datetime
import pytz
import numpy as np

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
    # 1. Vérifier si le pseudo est déjà utilisé
    existing_user_response = supabase.table("User").select("pseudo").eq("pseudo", pseudo).execute()

    if existing_user_response.data:
        raise Exception("Le pseudo est déjà utilisé, veuillez en choisir un autre.")

    # 2. Hasher le mot de passe
    mot_de_passe_hash = f.hash_password(mot_de_passe)

    # 3. Ajouter dans la table User
    user_response = supabase.table("User").insert({
        "pseudo": pseudo,
        "mot_de_passe": mot_de_passe_hash,
        "adresse_mail": adresse_mail  # si ce champ existe
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

    print(f"Utilisateur {pseudo} ajouté avec id {id_user} et solde initial 110")

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

def finir_contrat(supabase,id_joueur: str, id_equipe: str):
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
        supabase.table("Contrat") \
            .update({"END": now}) \
            .eq("id_contrat", id_contrat) \
            .execute()
        print(f"✅ Contrat {id_contrat} terminé pour joueur {id_joueur} avec {id_equipe} à {now}")
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


def ajouter_match(supabase, game_code: int, season: int, id_equipe_1: str, id_equipe_2: str, 
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

def ajouter_performance(supabase, season: int, id_match: int, id_contrat: int, per: int):
    # Corriger un PER négatif à 0
    if per < 0:
        print(f"⚠️ PER négatif détecté pour contrat {id_contrat}, ajusté à 0.")
        per = 0

    # Insertion de la performance
    result = supabase.table("Performance").insert({
        "season": season,
        "id_match": id_match,
        "id_contrat": id_contrat,
        "PER": per
    }).execute()

    if result.data:
        print(f"✅ Performance ajoutée : contrat {id_contrat}, match {id_match}, PER = {per}")
    else:
        print("❌ Échec de l’ajout de la performance.")

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
            if ggs['local.score'].to_list()[0] == 0 and ggs['road.score'].to_list()[0] == 0:
                print(f"⚠️ Match {game_code} non joué, pas de données disponibles.")
                continue

            boxscore = bs.get_player_boxscore_stats_data(season=season, gamecode=game_code)
            
            # 🔹 Formatage de la date
            date = ggs["date"].to_list()[0]
            
            # 🔹 Nettoyage du boxscore
            boxscore = boxscore[
                (boxscore['Minutes'] != "DNP") &
                (boxscore["Player_ID"] != "Team") &
                (boxscore["Player_ID"] != "Total")
            ][["Player_ID", "Player", "Team", "Valuation"]].reset_index(drop=True)

            id_update = list(set(boxscore["Player_ID"].to_list() + id_update))

            # 🔹 Équipes
            id_equipe_local = ggs['local.club.code'].to_list()[0]
            nom_local = ggs['local.club.name'].to_list()[0]
            id_equipe_road = ggs['road.club.code'].to_list()[0]
            nom_road = ggs['road.club.name'].to_list()[0]

            # 🔹 Ajout des équipes
            ajouter_equipe(supabase, id_equipe_local, nom_local)
            ajouter_equipe(supabase, id_equipe_road, nom_road)

            # 🔹 Ajout du match
            ajouter_match(
                supabase, game_code, season,
                id_equipe_local, id_equipe_road,
                ggs['local.score'].to_list()[0],
                ggs['road.score'].to_list()[0],
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
                        ajouter_performance(supabase, season, game_code, id_contrat, perf)
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
