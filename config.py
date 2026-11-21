# Réglages de la bibliothèque : on peut les modifier ici sans toucher au reste du code.

DUREE_PRET_JOURS = 14            # durée d'un emprunt
LIMITE_EMPRUNTS = 3              # livres empruntés en même temps par un étudiant

PENALITE_PAR_JOUR = 200          # en FCFA, par jour de retard
POURCENTAGE_ABIME = 30           # % du prix du livre si rendu abîmé
POURCENTAGE_PERDU = 100          # % du prix du livre si perdu ou détruit

PRIX_ABONNEMENT = 5000           # en FCFA
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