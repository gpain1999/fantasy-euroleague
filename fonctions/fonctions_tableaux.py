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
    perf_res = supabase.table("vue_tableau_recap") \
        .select("id_contrat, date, PER, nom, prenom, nom_equipe") \
        .in_("id_contrat", contrats_possedes) \
        .eq("rang", 1) \
        .execute()

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
    for row in achats_res.data:
        contrat = row["id_contrat"]
        if contrat not in prix_dict:
            prix_dict[contrat] = row["prix"]

    # 5. Construire le tableau final
    effectif = []
    for row in perf_res.data:
        id_contrat = row["id_contrat"]
        effectif.append({
            "id_contrat": id_contrat,
            "Joueur": f"{row['prenom']} {row['nom']}",
            "Équipe": row["nom_equipe"],
            "Valeur actuelle": valeurs_dict.get(id_contrat, "?"),
            "Prix d’achat": prix_dict.get(id_contrat, "?"),
            "Dernier match": row["date"],
            "Dernier PER": row["PER"]
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

    perf_res = supabase.table("vue_tableau_recap") \
        .select("id_contrat, date, PER, nom,prenom,nom_equipe") \
        .in_("id_contrat", contrats_disponibles) \
        .eq("rang", 1) \
        .execute()


    # Étape 1 : extraire les id_contrat
    id_contrats = [row["id_contrat"] for row in perf_res.data]

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
    for row in perf_res.data:
        row["valeur_actuelle"] = valeurs_dict.get(row["id_contrat"], "?")
        effectif.append({
            "id_contrat": row["id_contrat"],
            "Joueur": f"{row['prenom']} {row['nom']}",
            "Équipe": row["nom_equipe"],
            "Valeur actuelle":  row["valeur_actuelle"],
            "Dernier match": row["date"],
            "Dernier PER": row["PER"]
        })
    return effectif