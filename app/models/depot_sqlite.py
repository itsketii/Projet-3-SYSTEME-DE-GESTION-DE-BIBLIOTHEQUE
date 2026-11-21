import os
import sqlite3
from datetime import date, timedelta

from app.models.entites import Livre, Exemplaire, Etudiant, Emprunt, Penalite, Paiement


class DepotSQLite:
    """Seule classe du projet qui parle à la base de données."""

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
                prix    INTEGER NOT NULL,
                categorie TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS exemplaires (
                code        TEXT PRIMARY KEY,
                code_livre  TEXT NOT NULL REFERENCES livres(code)
            );
            CREATE TABLE IF NOT EXISTS etudiants (
                matricule       TEXT PRIMARY KEY,
                nom             TEXT NOT NULL,
                fin_abonnement  TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS emprunts (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                code_exemplaire TEXT NOT NULL REFERENCES exemplaires(code),
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
                date       TEXT NOT NULL,
                mode       TEXT NOT NULL
            );
        """)
        self.connexion.commit()

    def inserer_donnees_demo(self):
        # On n'insère les données de démonstration que si la base est vide
        nb_livres = self.connexion.execute("SELECT COUNT(*) FROM livres").fetchone()[0]
        if nb_livres > 0:
            return

        # (code, titre, auteur, année, prix en FCFA, catégorie, nombre d'exemplaires)
        catalogue = [
            ("L001", "Une si longue lettre", "Mariama Bâ", 1979, 3500, "Littérature africaine", 2),
            ("L002", "Les Soleils des indépendances", "Ahmadou Kourouma", 1968, 4000, "Littérature ivoirienne", 3),
            ("L003", "L'Enfant noir", "Camara Laye", 1953, 3000, "Littérature africaine", 2),
            ("L004", "Allah n'est pas obligé", "Ahmadou Kourouma", 2000, 4500, "Littérature ivoirienne", 2),
            ("L005", "Le Petit Prince", "Antoine de Saint-Exupéry", 1943, 3000, "Jeunesse", 3),
            ("L006", "Les Misérables", "Victor Hugo", 1862, 6000, "Littérature française classique", 2),
            ("L007", "Germinal", "Émile Zola", 1885, 4000, "Littérature française classique", 2),
            ("L008", "Les Bouts de bois de Dieu", "Sembène Ousmane", 1960, 3500, "Littérature africaine", 1),
            ("L009", "Climbié", "Bernard Dadié", 1956, 3500, "Littérature ivoirienne", 2),
            ("L010", "Un nègre à Paris", "Bernard Dadié", 1959, 3500, "Littérature ivoirienne", 1),
            ("L011", "Le Monde s'effondre", "Chinua Achebe", 1958, 4000, "Littérature africaine", 2),
            ("L012", "Le Rouge et le Noir", "Stendhal", 1830, 4500, "Littérature française classique", 1),
            ("L013", "Le Cid", "Pierre Corneille", 1637, 2500, "Théâtre", 2),
            ("L014", "Le Malade imaginaire", "Molière", 1673, 2500, "Théâtre", 2),
            ("L015", "Antigone", "Jean Anouilh", 1944, 3000, "Théâtre", 1),
            ("L016", "Les Fleurs du mal", "Charles Baudelaire", 1857, 3000, "Poésie", 1),
            ("L017", "Chants d'ombre", "Léopold Sédar Senghor", 1945, 3000, "Poésie", 1),
            ("L018", "Hunger Games", "Suzanne Collins", 2008, 5000, "Fantasy et science-fiction", 3),
            ("L019", "Harry Potter à l'école des sorciers", "J. K. Rowling", 1997, 6000, "Fantasy et science-fiction", 2),
            ("L020", "Le Seigneur des anneaux : La Communauté de l'anneau", "J. R. R. Tolkien", 1954, 6500, "Fantasy et science-fiction", 1),
            ("L021", "Le Petit Nicolas", "René Goscinny et Jean-Jacques Sempé", 1960, 3000, "Jeunesse", 2),
            ("L022", "Apprendre à programmer avec Python 3", "Gérard Swinnen", 2012, 8000, "Informatique", 3),
            ("L023", "Le Langage C", "Brian Kernighan et Dennis Ritchie", 1978, 12000, "Informatique", 1),
            ("L024", "Le Bon Usage", "Maurice Grevisse", 1936, 15000, "Manuels et études", 1),
        ]
        for code, titre, auteur, annee, prix, categorie, nb_exemplaires in catalogue:
            self.connexion.execute(
                "INSERT INTO livres (code, titre, auteur, annee, prix, categorie) VALUES (?, ?, ?, ?, ?, ?)",
                (code, titre, auteur, annee, prix, categorie),
            )
            for numero in range(1, nb_exemplaires + 1):
                self.connexion.execute(
                    "INSERT INTO exemplaires (code, code_livre) VALUES (?, ?)",
                    (f"{code}-{numero:02d}", code),
                )

        aujourdhui = date.today()
        etudiants = [
            ("IIT-001", "Aya Konan", (aujourdhui + timedelta(days=365)).isoformat()),
            ("IIT-002", "Yao Kouassi", (aujourdhui + timedelta(days=200)).isoformat()),
            ("IIT-003", "Fatou Traoré", (aujourdhui - timedelta(days=30)).isoformat()),
        ]
        self.connexion.executemany(
            "INSERT INTO etudiants (matricule, nom, fin_abonnement) VALUES (?, ?, ?)",
            etudiants,
        )
        self.connexion.commit()

    # ---------- LIVRES ET EXEMPLAIRES ----------

    def chercher_livres(self, mot_cle="", categorie=None):
        requete = (
            "SELECT code, titre, auteur, annee, prix, categorie FROM livres "
            "WHERE (titre LIKE ? OR auteur LIKE ?)"
        )
        modele = f"%{mot_cle}%"
        valeurs = [modele, modele]
        if categorie is not None:
            requete += " AND categorie = ?"
            valeurs.append(categorie)
        requete += " ORDER BY code"
        lignes = self.connexion.execute(requete, valeurs).fetchall()
        return [Livre(*ligne) for ligne in lignes]

    def trouver_livre(self, code):
        ligne = self.connexion.execute(
            "SELECT code, titre, auteur, annee, prix, categorie FROM livres WHERE code = ?",
            (code,),
        ).fetchone()
        if ligne is None:
            return None
        return Livre(*ligne)

    def trouver_exemplaire(self, code):
        ligne = self.connexion.execute(
            "SELECT code, code_livre FROM exemplaires WHERE code = ?",
            (code,),
        ).fetchone()
        if ligne is None:
            return None
        return Exemplaire(*ligne)

    def exemplaires_du_livre(self, code_livre):
        lignes = self.connexion.execute(
            "SELECT code, code_livre FROM exemplaires WHERE code_livre = ? ORDER BY code",
            (code_livre,),
        ).fetchall()
        return [Exemplaire(*ligne) for ligne in lignes]

    def exemplaires_disponibles(self, code_livre):
        # Disponible = aucun emprunt en cours ET pas déclaré perdu
        lignes = self.connexion.execute(
            "SELECT e.code, e.code_livre FROM exemplaires e "
            "WHERE e.code_livre = ? AND NOT EXISTS ("
            "  SELECT 1 FROM emprunts m WHERE m.code_exemplaire = e.code "
            "  AND (m.date_retour IS NULL OR m.etat_retour = 'perdu')"
            ") ORDER BY e.code",
            (code_livre,),
        ).fetchall()
        return [Exemplaire(*ligne) for ligne in lignes]

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

    # ---------- EMPRUNTS ----------

    def _emprunt_depuis_ligne(self, ligne):
        return Emprunt(
            code_exemplaire=ligne[1],
            matricule=ligne[2],
            date_emprunt=date.fromisoformat(ligne[3]),
            date_limite=date.fromisoformat(ligne[4]),
            date_retour=date.fromisoformat(ligne[5]) if ligne[5] else None,
            etat_retour=ligne[6],
            id=ligne[0],
        )

    def ajouter_emprunt(self, emprunt):
        curseur = self.connexion.execute(
            "INSERT INTO emprunts (code_exemplaire, matricule, date_emprunt, date_limite) "
            "VALUES (?, ?, ?, ?)",
            (
                emprunt.code_exemplaire,
                emprunt.matricule,
                emprunt.date_emprunt.isoformat(),
                emprunt.date_limite.isoformat(),
            ),
        )
        self.connexion.commit()
        return curseur.lastrowid

    def emprunt_en_cours_de_l_exemplaire(self, code_exemplaire):
        ligne = self.connexion.execute(
            "SELECT id, code_exemplaire, matricule, date_emprunt, date_limite, date_retour, etat_retour "
            "FROM emprunts WHERE code_exemplaire = ? AND (date_retour IS NULL OR etat_retour = 'perdu')",
            (code_exemplaire,),
        ).fetchone()
        if ligne is None:
            return None
        return self._emprunt_depuis_ligne(ligne)

    def emprunts_en_cours_de(self, matricule):
        lignes = self.connexion.execute(
            "SELECT id, code_exemplaire, matricule, date_emprunt, date_limite, date_retour, etat_retour "
            "FROM emprunts WHERE matricule = ? AND date_retour IS NULL",
            (matricule,),
        ).fetchall()
        return [self._emprunt_depuis_ligne(ligne) for ligne in lignes]

    def tous_les_emprunts_en_cours(self):
        lignes = self.connexion.execute(
            "SELECT id, code_exemplaire, matricule, date_emprunt, date_limite, date_retour, etat_retour "
            "FROM emprunts WHERE date_retour IS NULL ORDER BY date_limite"
        ).fetchall()
        return [self._emprunt_depuis_ligne(ligne) for ligne in lignes]

    def enregistrer_retour(self, id_emprunt, date_retour, etat):
        self.connexion.execute(
            "UPDATE emprunts SET date_retour = ?, etat_retour = ? WHERE id = ?",
            (date_retour.isoformat(), etat, id_emprunt),
        )
        self.connexion.commit()

    # ---------- PENALITES ----------

    def _penalite_depuis_ligne(self, ligne):
        return Penalite(
            id_emprunt=ligne[1],
            matricule=ligne[2],
            montant=ligne[3],
            motif=ligne[4],
            payee=bool(ligne[5]),
            id=ligne[0],
        )

    def ajouter_penalite(self, penalite):
        self.connexion.execute(
            "INSERT INTO penalites (id_emprunt, matricule, montant, motif) "
            "VALUES (?, ?, ?, ?)",
            (penalite.id_emprunt, penalite.matricule, penalite.montant, penalite.motif),
        )
        self.connexion.commit()

    def penalites_impayees(self, matricule):
        lignes = self.connexion.execute(
            "SELECT id, id_emprunt, matricule, montant, motif, payee "
            "FROM penalites WHERE matricule = ? AND payee = 0",
            (matricule,),
        ).fetchall()
        return [self._penalite_depuis_ligne(ligne) for ligne in lignes]

    def marquer_penalite_payee(self, id_penalite):
        self.connexion.execute(
            "UPDATE penalites SET payee = 1 WHERE id = ?",
            (id_penalite,),
        )
        self.connexion.commit()

    # ---------- PAIEMENTS ----------

    def ajouter_paiement(self, paiement):
        curseur = self.connexion.execute(
            "INSERT INTO paiements (matricule, motif, montant, date, mode) VALUES (?, ?, ?, ?, ?)",
            (
                paiement.matricule,
                paiement.motif,
                paiement.montant,
                paiement.date.isoformat(),
                paiement.mode,
            ),
        )
        self.connexion.commit()
        return curseur.lastrowid

    def paiements_de(self, matricule):
        lignes = self.connexion.execute(
            "SELECT id, matricule, motif, montant, date, mode FROM paiements "
            "WHERE matricule = ? ORDER BY date",
            (matricule,),
        ).fetchall()
        return [
            Paiement(ligne[1], ligne[2], ligne[3], date.fromisoformat(ligne[4]), ligne[5], ligne[0])
            for ligne in lignes
        ]

    def total_encaisse(self):
        return self.connexion.execute(
            "SELECT COALESCE(SUM(montant), 0) FROM paiements"
        ).fetchone()[0]