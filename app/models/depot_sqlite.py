import os
import sqlite3
from datetime import date, timedelta


from app.models.entites import Livre, Etudiant


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

    # ---------- LIVRES ----------

    def chercher_livres(self, mot_cle):
        modele = f"%{mot_cle}%"
        lignes = self.connexion.execute(
            "SELECT code, titre, auteur, annee, prix FROM livres "
            "WHERE titre LIKE ? OR auteur LIKE ? ORDER BY code",
            (modele, modele),
        ).fetchall()
        return [Livre(*ligne) for ligne in lignes]

    def trouver_livre(self, code):
        ligne = self.connexion.execute(
            "SELECT code, titre, auteur, annee, prix FROM livres WHERE code = ?",
            (code,),
        ).fetchone()
        if ligne is None:
            return None
        return Livre(*ligne)

    # ---------- ETUDIANTS ----------

    def trouver_etudiant(self, matricule):
        ligne = self.connexion.execute(
            "SELECT matricule, nom, fin_abonnement FROM etudiants WHERE matricule = ?",
            (matricule,),
        ).fetchone()
        if ligne is None:
            return None
        return Etudiant(ligne[0], ligne[1], date.fromisoformat(ligne[2]))

    def ajouter_etudiant(self, etudiant):
        self.connexion.execute(
            "INSERT INTO etudiants (matricule, nom, fin_abonnement) VALUES (?, ?, ?)",
            (etudiant.matricule, etudiant.nom, etudiant.fin_abonnement.isoformat()),
        )
        self.connexion.commit()

    def prochain_matricule(self):
        nb = self.connexion.execute("SELECT COUNT(*) FROM etudiants").fetchone()[0]
        return f"IIT-{nb + 1:03d}"

    def mettre_a_jour_abonnement(self, matricule, nouvelle_fin):
        self.connexion.execute(
            "UPDATE etudiants SET fin_abonnement = ? WHERE matricule = ?",
            (nouvelle_fin.isoformat(), matricule),
        )
        self.connexion.commit()