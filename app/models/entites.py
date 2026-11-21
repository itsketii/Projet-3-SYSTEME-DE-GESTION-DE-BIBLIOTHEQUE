from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Livre:
    code: str      # identifiant unique
    titre: str
    auteur: str
    annee: int
    prix: int      # en FCFA, sert à calculer les pénalités
    categorie: str # ex : "Littérature ivoirienne" (voir config.CATEGORIES)


@dataclass
class Exemplaire:
    code: str        # ex : "L002-01" (code de l'exemplaire)
    code_livre: str  # le livre dont c'est un exemplaire


@dataclass
class Etudiant:
    matricule: str         # ex : "IIT-001"
    nom: str
    fin_abonnement: date   # dernier jour de l'abonnement


@dataclass
class Emprunt:
    code_exemplaire: str
    matricule: str
    date_emprunt: date
    date_limite: date                    # emprunt + 14 jours
    date_retour: date | None   # None tant que le livre n'est pas rendu
    etat_retour: str | None    # "bon", "abime" ou "perdu"
    id: int | None             # donné par la base de données


@dataclass
class Penalite:
    id_emprunt: int
    matricule: str
    montant: int           # en FCFA
    motif: str             # "retard", "abime" ou "perdu"
    payee: bool = False    # True quand l'étudiant a payé
    id: int | None = None


@dataclass
class Paiement:
    matricule: str
    motif: str             # "abonnement", "emprunt" ou "penalite"
    montant: int
    date: date
    mode: str              # "Espèces", "Wave", "Orange Money"...
    id: int | None