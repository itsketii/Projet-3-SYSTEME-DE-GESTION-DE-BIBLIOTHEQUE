from dataclasses import dataclass
from datetime import date


@dataclass
class Livre:
    code: str
    titre: str
    auteur: str
    annee: int
    prix: int


@dataclass
class Etudiant:
    matricule: str
    nom: str
    fin_abonnement: date


@dataclass
class Emprunt:
    code_livre: str
    matricule: str
    date_emprunt: date
    date_limite: date
    date_retour: date | None = None
    etat_retour: str | None = None
    id: int | None = None


@dataclass
class Penalite:
    id_emprunt: int
    matricule: str
    montant: int
    motif: str
    payee: bool = False
    id: int | None = None


@dataclass
class Paiement:
    matricule: str
    motif: str  
    montant: int
    date: date
    id: int | None = None