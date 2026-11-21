# Réglages de la bibliothèque : on peut les modifier ici sans toucher au reste du code.

DUREE_PRET_JOURS = 14            # durée d'un emprunt
LIMITE_EMPRUNTS = 3              # livres empruntés en même temps par un étudiant

PENALITE_PAR_JOUR = 200          # en FCFA, par jour de retard
POURCENTAGE_ABIME = 30           # % du prix du livre si rendu abîmé
POURCENTAGE_PERDU = 100          # % du prix du livre si perdu ou détruit

# Catégories de membres : préfixe du matricule et prix de l'abonnement annuel (FCFA)
CATEGORIES_MEMBRES = {
    "eleve": {"libelle": "Élève (collège, lycée)", "prefixe": "ELV", "prix_abonnement": 2000},
    "etudiant": {"libelle": "Étudiant", "prefixe": "IIT", "prix_abonnement": 3000},
    "externe": {"libelle": "Personne extérieure", "prefixe": "EXT", "prix_abonnement": 5000},
}

DUREE_ABONNEMENT_JOURS = 365     # un an
PRIX_EMPRUNT_OCCASIONNEL = 500   # en FCFA, pour emprunter sans abonnement valide

MODE_ESPECES = "Espèces"
MODES_PAIEMENT = [MODE_ESPECES, "Carte bancaire", "Wave", "Orange Money", "MTN Money", "Moov Money"]

CATEGORIES = [
    "Littérature ivoirienne",
    "Littérature africaine",
    "Littérature française classique",
    "Théâtre",
    "Poésie",
    "Fantasy et science-fiction",
    "Jeunesse",
    "Informatique",
    "Manuels et études",
]

PAIEMENT_MINIMUM_ABONNEMENT = 1000   # FCFA : montant minimum pour un abonnement partiel
RAPPEL_EXPIRATION_JOURS = 7          # prévenir les membres dont l'abonnement expire dans ce délai