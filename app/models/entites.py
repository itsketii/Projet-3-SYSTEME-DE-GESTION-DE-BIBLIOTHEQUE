from dataclasses import dataclass
from typing import Optional


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
    fin_abonnement: str


@dataclass
class Emprunt:
    code_livre: str
    matricule: str
    date_emprunt: str
    date_limite: str
    date_retour: Optional[str] = None
    etat_retour: Optional[str] = None
    id: Optional[int] = None


@dataclass
class Penalite:
    id_emprunt: int
    matricule: str
    montant: int
    motif: str
    payee: bool = False
    id: Optional[int] = None


@dataclass
class Paiement:
    matricule: str
    motif: str
    montant: int
    date: str
    id: Optional[int] = None