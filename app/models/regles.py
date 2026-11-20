from datetime import timedelta

import config


def calculer_date_limite(date_emprunt):
    return date_emprunt + timedelta(days=config.DUREE_PRET_JOURS)


def abonnement_valide(fin_abonnement, aujourdhui):
    return fin_abonnement >= aujourdhui


def calculer_fin_abonnement(fin_actuelle, aujourdhui):
    # Si l'abonnement court encore, on prolonge à partir de sa fin (aucun jour perdu)
    depart = max(fin_actuelle, aujourdhui)
    return depart + timedelta(days=config.DUREE_ABONNEMENT_JOURS)


def est_en_retard(emprunt, aujourdhui):
    return emprunt.date_retour is None and aujourdhui > emprunt.date_limite


def jours_de_retard(date_limite, date_retour):
    return max(0, (date_retour - date_limite).days)


def penalite_retard(jours, prix_livre):
    return min(jours * config.PENALITE_PAR_JOUR, prix_livre)


def penalite_etat(etat, prix_livre):
    if etat == "abime":
        return prix_livre * config.POURCENTAGE_ABIME // 100
    if etat == "perdu":
        return prix_livre * config.POURCENTAGE_PERDU // 100
    return 0


def penalites_au_retour(date_limite, date_retour, etat, prix_livre):
    """Renvoie la liste des pénalités à créer : [(motif, montant), ...]"""
    if etat == "perdu":
        # Livre perdu : on paie le livre, pas de pénalité de retard en plus
        return [("perdu", penalite_etat("perdu", prix_livre))]

    penalites = []
    montant_retard = penalite_retard(jours_de_retard(date_limite, date_retour), prix_livre)
    if montant_retard > 0:
        penalites.append(("retard", montant_retard))
    montant_etat = penalite_etat(etat, prix_livre)
    if montant_etat > 0:
        penalites.append(("abime", montant_etat))
    return penalites


def raison_de_refus(livre, emprunt_en_cours_du_livre, nb_emprunts_etudiant, a_des_penalites):
    """Renvoie le message de refus, ou None si l'emprunt est autorisé."""
    if emprunt_en_cours_du_livre is not None:
        if emprunt_en_cours_du_livre.etat_retour == "perdu":
            return f"Impossible : Le livre « {livre.titre} » est perdu ou détruit."
        return f"Impossible : Le livre « {livre.titre} » est déjà emprunté."
    if nb_emprunts_etudiant >= config.LIMITE_EMPRUNTS:
        return f"Impossible : limite de {config.LIMITE_EMPRUNTS} livres empruntés atteinte."
    if a_des_penalites:
        return "Impossible : des pénalités sont à régler avant un nouvel emprunt."
    return None