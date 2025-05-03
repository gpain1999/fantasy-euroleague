import pytz


    

def get_derniere_performance(supabase, id_contrat: int):
    # Étape 1 : récupérer les performances liées à ce contrat
    perf_res = supabase.table("Performance") \
        .select("id_match, season, PER") \
        .eq("id_contrat", id_contrat) \
        .execute()

    if not perf_res.data:
        return None, None

    # Liste pour stocker (date, PER)
    performances = []

    for p in perf_res.data:
        id_match = p["id_match"]
        season = p["season"]
        per = p["PER"]

        # Étape 2 : récupérer la date du match
        match_res = supabase.table("Match") \
            .select("date") \
            .eq("id_match", id_match) \
            .eq("season", season) \
            .limit(1) \
            .execute()

        if match_res.data:
            date = match_res.data[0]["date"]
            performances.append((date, per))

    # Trier par date DESC
    performances.sort(reverse=True)

    if performances:
        date, per = performances[0]
        return date, per
    else:
        return None, None


def afficher_effectif(supabase, id_user: int):
    # 1. Récupérer les contrats actifs de l'utilisateur
    possession_res = supabase.table("Possession") \
        .select("id_contrat") \
        .eq("id_user", id_user) \
        .is_("END", None) \
        .execute()

    if not possession_res.data:
        print("ℹ️ Aucun joueur dans l’effectif.")
        return []

    contrats_possedes = [p["id_contrat"] for p in possession_res.data]

    # 2. Récupérer les infos depuis vue_tableau_recap
    perf_res1 = supabase.table("vue_tableau_recap") \
        .select("id_contrat, date, PER, nom, prenom, nom_equipe") \
        .in_("id_contrat", contrats_possedes) \
        .eq("rang", 1) \
        .execute()
    

    perf_res4 = supabase.table("vue_tableau_recap") \
        .select("id_contrat, PER") \
        .in_("id_contrat", contrats_possedes) \
        .eq("rang", 4) \
        .execute()
    # Indexé par id_contrat pour jointure rapide
    perf1_dict = {}
    for row in perf_res1.data:
        perf1_dict[row["id_contrat"]] = {
            "PER_1": row["PER"],
            "Dernier match": row["date"],
            "Joueur": f"{row['prenom']} {row['nom']}",
            "Équipe": row["nom_equipe"]
        }

    perf4_dict = {}
    for row in perf_res4.data:
        perf4_dict[row["id_contrat"]] = {
            "PER_4": row["PER"]
        }

    perf_res = []

    for id_contrat in contrats_possedes:
        if id_contrat not in perf1_dict:
            continue  # ignore si pas de match récent

        row = {
            "id_contrat": id_contrat,
            **perf1_dict[id_contrat],
            **perf4_dict.get(id_contrat, {"PER_4": "-"})  # si pas de PER_4
        }

        perf_res.append(row)

    # 3. Récupérer les valeurs actuelles
    valeurs_res = supabase.table("Valeur_Actuelle") \
        .select("id_contrat, valeur") \
        .in_("id_contrat", contrats_possedes) \
        .order("date", desc=True) \
        .execute()

    valeurs_dict = {}
    for row in valeurs_res.data:
        contrat = row["id_contrat"]
        if contrat not in valeurs_dict:
            valeurs_dict[contrat] = row["valeur"]

    # 4. Récupérer les prix d’achat
    achats_res = supabase.table("Transaction") \
        .select("id_contrat, prix, datetime") \
        .eq("id_user", id_user) \
        .eq("type_transaction", True) \
        .in_("id_contrat", contrats_possedes) \
        .order("datetime", desc=True) \
        .execute()

    prix_dict = {}
    date_achats = {}
    for row in achats_res.data:
        contrat = row["id_contrat"]
        if contrat not in prix_dict:
            prix_dict[contrat] = row["prix"]
        if contrat not in date_achats:
            date_achats[contrat] = row["datetime"]

    # 5. Construire le tableau final
    effectif = []
    for row in perf_res:
        id_contrat = row["id_contrat"]
        effectif.append({
            "id_contrat": id_contrat,
            "Joueur": f"{row['Joueur']}",
            "Équipe": row["Équipe"],
            "Valeur actuelle": valeurs_dict.get(id_contrat, "?"),
            "Prix d’achat": prix_dict.get(id_contrat, "?"),
            "Date d’achat": date_achats.get(id_contrat, "?"),
            "Dernier match": row["Dernier match"],
            "Dernier PER": row["PER_1"],
            "PER_4": row["PER_4"]
        })

    return effectif


def afficher_joueurs_disponibles(supabase, id_user: int):
    # 1. Récupérer tous les contrats actifs
    contrats_actifs_res = supabase.table("Contrat") \
        .select("id_contrat") \
        .is_("END", None) \
        .execute()

    if not contrats_actifs_res.data:
        return []

    # 2. Récupérer les contrats déjà possédés par l'utilisateur
    possedes_res = supabase.table("Possession") \
        .select("id_contrat") \
        .eq("id_user", id_user) \
        .is_("END", None) \
        .execute()

    contrats_possedes = {p["id_contrat"] for p in possedes_res.data} if possedes_res.data else set()

    # 3. Filtrer les contrats disponibles
    contrats_disponibles = [
        contrat["id_contrat"]
        for contrat in contrats_actifs_res.data
        if contrat["id_contrat"] not in contrats_possedes
    ]
    # 2. Récupérer les infos depuis vue_tableau_recap
    perf_res1 = supabase.table("vue_tableau_recap") \
        .select("id_contrat, date, PER, nom, prenom, nom_equipe") \
        .in_("id_contrat", contrats_disponibles) \
        .eq("rang", 1) \
        .execute()
    

    perf_res4 = supabase.table("vue_tableau_recap") \
        .select("id_contrat, PER") \
        .in_("id_contrat", contrats_disponibles) \
        .eq("rang", 4) \
        .execute()
    # Indexé par id_contrat pour jointure rapide
    perf1_dict = {}
    for row in perf_res1.data:
        perf1_dict[row["id_contrat"]] = {
            "PER_1": row["PER"],
            "Dernier match": row["date"],
            "Joueur": f"{row['prenom']} {row['nom']}",
            "Équipe": row["nom_equipe"]
        }

    perf4_dict = {}
    for row in perf_res4.data:
        perf4_dict[row["id_contrat"]] = {
            "PER_4": row["PER"]
        }

    perf_res = []

    for id_contrat in contrats_disponibles:
        if id_contrat not in perf1_dict:
            continue  # ignore si pas de match récent

        row = {
            "id_contrat": id_contrat,
            **perf1_dict[id_contrat],
            **perf4_dict.get(id_contrat, {"PER_4": "-"})  # si pas de PER_4
        }

        perf_res.append(row)




    # Étape 1 : extraire les id_contrat
    id_contrats = [row["id_contrat"] for row in perf_res]

    # Étape 2 : récupérer les valeurs actuelles les plus récentes
    valeurs_res = supabase.table("Valeur_Actuelle") \
        .select("id_contrat, valeur") \
        .in_("id_contrat", id_contrats) \
        .order("date", desc=True) \
        .execute()

    # Étape 3 : garder la valeur la plus récente par contrat
    valeurs_dict = {}
    for row in valeurs_res.data:
        contrat = row["id_contrat"]
        if contrat not in valeurs_dict:
            valeurs_dict[contrat] = row["valeur"]

    effectif = []
    # Étape 4 : enrichir perf_res
    for row in perf_res:
        row["valeur_actuelle"] = valeurs_dict.get(row["id_contrat"], "?")
        effectif.append({
            "id_contrat": row["id_contrat"],
            "Joueur": f"{row['Joueur']}",
            "Équipe": row["Équipe"],
            "Valeur actuelle":  row["valeur_actuelle"],
            "Dernier match": row["Dernier match"],
            "Dernier PER": row["PER_1"],
            "PER_4": row["PER_4"]
        })
    return effectif

def afficher_solde_actuel(supabase, id_user: int):
    # 1. Récupérer le dernier solde pour cet utilisateur
    solde_res = supabase.table("Banque") \
        .select("solde") \
        .eq("id_user", id_user) \
        .order("datetime", desc=True) \
        .limit(1) \
        .execute()

    if solde_res.data:
        return solde_res.data[0]["solde"]
    else:
        print("❌ Aucun solde trouvé pour cet utilisateur.")
        return None

def recuperations_statistiques(supabase, id_contrat: int):
    # 2. Récupérer les infos depuis vue_tableau_recap
    perf_res = supabase.table("vue_tableau_recap") \
        .select("id_contrat, date, PER, nom, prenom, nom_equipe,rang,id_joueur") \
        .eq("id_contrat", id_contrat) \
        .execute()
    
    # Trier les performances par rang croissant
    perf_tries = sorted(perf_res.data, key=lambda x: x["rang"])

    # Extraire les listes
    per_list = []
    rang_list = []
    date_list = []
    print(perf_tries[0])
    for row in perf_tries:
        if isinstance(row["PER"], (int, float)):  # filtre valeurs valides
            per_list.append(row["PER"])
            rang_list.append(row["rang"])
            date_list.append(row["date"])

    # Extraire les infos de base (nom joueur, équipe) depuis la 1ère ligne
    if perf_tries:
        joueur_info = {
            "nom": perf_tries[0]["nom"],
            "prenom": perf_tries[0]["prenom"],
            "nom_equipe": perf_tries[0]["nom_equipe"],
            "id_joueur": perf_tries[0]["id_joueur"],
        }
        joueur_stat = {
            "PER": per_list,
            "Rang": rang_list,
            "Date": date_list
        }
    else:
        joueur_info = {}
        joueur_stat = { }

    return joueur_info, joueur_stat  