import os
import sqlite3
from datetime import date, timedelta


class DepotSQLite:
    """La (seule) classe du projet qui parle à la base de données."""

    def __init__(self, chemin="data/bibliotheque.db"):
        # Crée le dossier "data" s'il n'existe pas encore
        os.makedirs(os.path.dirname(chemin), exist_ok=True)
        # Ouvre la base (le fichier est créé automatiquement s'il n'existe pas)
        self.connexion = sqlite3.connect(chemin)
        self.creer_tables()
        self.inserer_donnees_demo()

    def creer_tables(self):
        self.connexion.executescript("""
            CREATE TABLE IF NOT EXISTS livres (
                code    TEXT PRIMARY KEY,
                titre   TEXT NOT NULL,
                auteur  TEXT NOT NULL,
                annee   INTEGER,
                prix    INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS etudiants (
                matricule       TEXT PRIMARY KEY,
                nom             TEXT NOT NULL,
                fin_abonnement  TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS emprunts (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                code_livre    TEXT NOT NULL REFERENCES livres(code),
                matricule     TEXT NOT NULL REFERENCES etudiants(matricule),
                date_emprunt  TEXT NOT NULL,
                date_limite   TEXT NOT NULL,
                date_retour   TEXT,
                etat_retour   TEXT
            );
            CREATE TABLE IF NOT EXISTS penalites (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                id_emprunt  INTEGER NOT NULL REFERENCES emprunts(id),
                matricule   TEXT NOT NULL REFERENCES etudiants(matricule),
                montant     INTEGER NOT NULL,
                motif       TEXT NOT NULL,
                payee       INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS paiements (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                matricule  TEXT NOT NULL REFERENCES etudiants(matricule),
                motif      TEXT NOT NULL,
                montant    INTEGER NOT NULL,
                date       TEXT NOT NULL
            );
        """)
        self.connexion.commit()

    def inserer_donnees_demo(self):
        # On n'insère les données de démonstration que si la base est vide
        nb_livres = self.connexion.execute("SELECT COUNT(*) FROM livres").fetchone()[0]
        if nb_livres > 0:
            return

        livres = [
            ("L001", "Une si longue lettre", "Mariama Bâ", 1979, 3500),
            ("L002", "Les Soleils des indépendances", "Ahmadou Kourouma", 1968, 4000),
            ("L003", "L'Enfant noir", "Camara Laye", 1953, 3000),
            ("L004", "Allah n'est pas obligé", "Ahmadou Kourouma", 2000, 4500),
            ("L005", "Le Petit Prince", "Antoine de Saint-Exupéry", 1943, 3000),
            ("L006", "Les Misérables", "Victor Hugo", 1862, 6000),
            ("L007", "Germinal", "Émile Zola", 1885, 4000),
            ("L008", "Les Bouts de bois de Dieu", "Sembène Ousmane", 1960, 3500),
        ]
        self.connexion.executemany(
            "INSERT INTO livres (code, titre, auteur, annee, prix) VALUES (?, ?, ?, ?, ?)",
            livres,
        )

        aujourdhui = date.today()
        etudiants = [
            ("IIT-001", "Aya Konan", (aujourdhui + timedelta(days=365)).isoformat()),
            ("IIT-002", "Yao Kouassi", (aujourdhui + timedelta(days=200)).isoformat()),
            ("IIT-003", "Fatou Traoré", (aujourdhui - timedelta(days=30)).isoformat()),
            ("IIT-350", "Kouadio Ketsia", (aujourdhui - timedelta(days=10)).isoformat()),
        ]
        self.connexion.executemany(
            "INSERT INTO etudiants (matricule, nom, fin_abonnement) VALUES (?, ?, ?)",
            etudiants,
        )
        self.connexion.commit()