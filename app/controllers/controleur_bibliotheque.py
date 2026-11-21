import os
from datetime import date

import config
from app.models import regles
from app.models.entites import Emprunt, Etudiant, Livre, Paiement, Penalite

ETATS = {"bon": "Bon état", "abime": "Abîmé", "perdu": "Perdu ou détruit"}
MOTIFS = {"retard": "Retard", "abime": "Livre abîmé", "perdu": "Livre perdu ou détruit"}


class ControleurBibliotheque:
    """Relie la vue (console), les règles et le dépôt (base de données)."""

    def __init__(self, depot):
        self.depot = depot
        # Une lecture sur place dure une journée : on clôture celles des jours précédents
        self.depot.cloturer_lectures_avant(date.today())

    def _normaliser(self, texte):
        # " l002 " devient "L002" : on tolère les espaces et les minuscules
        return texte.strip().upper()

    # ---------- OPTION 1 : RECHERCHER UN LIVRE ----------

    def rechercher_livres(self, mot_cle, categorie=None):
        """Renvoie une liste de tuples (livre, nb_exemplaires, codes_disponibles)."""
        resultats = []
        for livre in self.depot.chercher_livres(mot_cle, categorie):
            nb_exemplaires = len(self.depot.exemplaires_du_livre(livre.code))
            disponibles = [e.code for e in self.depot.exemplaires_disponibles(livre.code)]
            resultats.append((livre, nb_exemplaires, disponibles))
        return resultats

    # ---------- OPTION 3 : RENDRE UN LIVRE ----------

    def rendre_livre(self, code_exemplaire, etat):
        """etat : "bon", "abime" ou "perdu". Renvoie (ok, message)."""
        code_exemplaire = self._normaliser(code_exemplaire)
        exemplaire = self.depot.trouver_exemplaire(code_exemplaire)
        if exemplaire is None:
            return False, f"Impossible : aucun exemplaire avec le code {code_exemplaire}."
        livre = self.depot.trouver_livre(exemplaire.code_livre)

        emprunt = self.depot.emprunt_en_cours_de_l_exemplaire(code_exemplaire)
        if emprunt is None:
            if self.depot.lecture_en_cours_de(code_exemplaire) is not None:
                return False, (
                    f"L'exemplaire {code_exemplaire} est en lecture sur place : "
                    "utilisez « Lecture sur place » pour le remettre en rayon."
                )
            return False, f"L'exemplaire {code_exemplaire} de « {livre.titre} » n'est pas emprunté : rien à rendre."
        if emprunt.date_retour is not None:
            return False, f"L'exemplaire {code_exemplaire} de « {livre.titre} » est déjà déclaré perdu ou détruit."

        etudiant = self.depot.trouver_etudiant(emprunt.matricule)
        aujourdhui = date.today()
        self.depot.enregistrer_retour(emprunt.id, aujourdhui, etat)

        penalites = regles.penalites_au_retour(emprunt.date_limite, aujourdhui, etat, livre.prix)
        total = 0
        for motif, montant in penalites:
            self.depot.ajouter_penalite(Penalite(emprunt.id, emprunt.matricule, montant, motif))
            total += montant

        jours = regles.jours_de_retard(emprunt.date_limite, aujourdhui)
        lignes = [
            f"Retour enregistré : « {livre.titre} » (exemplaire {code_exemplaire}).",
            "",
            f"--- REÇU DE RETOUR N° RET-{emprunt.id:04d} ---",
            f"Date : {aujourdhui.strftime('%d/%m/%Y')}",
            f"Étudiant : {etudiant.nom} ({etudiant.matricule})",
            f"Livre : {livre.titre} (exemplaire {code_exemplaire})",
            f"Emprunté le : {emprunt.date_emprunt.strftime('%d/%m/%Y')}",
            f"À rendre avant le : {emprunt.date_limite.strftime('%d/%m/%Y')}",
            f"État du livre : {ETATS[etat]}",
        ]
        if jours > 0 and etat != "perdu":
            lignes.append(f"Jours de retard : {jours}")
        if penalites:
            lignes.append("Pénalités à régler :")
            for motif, montant in penalites:
                lignes.append(f"  - {MOTIFS[motif]} : {montant} FCFA")
            lignes.append(f"Total à régler : {total} FCFA (menu Paiements)")
        else:
            lignes.append("Aucune pénalité.")
        return True, "\n".join(lignes)

    # ---------- OPTION 4 : CONSULTER LES RETARDS ----------

    def lister_retards(self):
        """Renvoie une liste de tuples (code_exemplaire, livre, etudiant, date_limite, jours, montant)."""
        aujourdhui = date.today()
        retards = []
        for emprunt in self.depot.tous_les_emprunts_en_cours():
            if regles.est_en_retard(emprunt, aujourdhui):
                exemplaire = self.depot.trouver_exemplaire(emprunt.code_exemplaire)
                livre = self.depot.trouver_livre(exemplaire.code_livre)
                etudiant = self.depot.trouver_etudiant(emprunt.matricule)
                jours = regles.jours_de_retard(emprunt.date_limite, aujourdhui)
                montant = regles.penalite_retard(jours, livre.prix)
                retards.append((emprunt.code_exemplaire, livre, etudiant, emprunt.date_limite, jours, montant))
        return retards

    # ---------- OPTION 2 : EMPRUNTER UN LIVRE ----------

    def verifier_emprunt(self, code_livre, matricule):
        """Renvoie (statut, message). Statut : "refus", "abonnement_expire" ou "ok"."""
        code_livre = self._normaliser(code_livre)
        matricule = self._normaliser(matricule)

        livre = self.depot.trouver_livre(code_livre)
        if livre is None:
            return "refus", f"Impossible : aucun livre avec le code {code_livre}."
        etudiant = self.depot.trouver_etudiant(matricule)
        if etudiant is None:
            return "refus", f"Impossible : aucun étudiant avec le matricule {matricule}."

        raison = regles.raison_de_refus(
            livre,
            len(self.depot.exemplaires_disponibles(code_livre)),
            len(self.depot.emprunts_en_cours_de(matricule)),
            len(self.depot.penalites_impayees(matricule)) > 0,
        )
        if raison is not None:
            return "refus", raison

        if not regles.abonnement_valide(etudiant.fin_abonnement, date.today()):
            fin = etudiant.fin_abonnement.strftime("%d/%m/%Y")
            return "abonnement_expire", (
                f"Votre abonnement a expiré le {fin}. "
                "Veuillez le renouveler ou payer cet emprunt à l'unité."
            )
        return "ok", ""

    def enregistrer_emprunt(self, code_livre, matricule):
        """Crée l'emprunt (à appeler après verifier_emprunt). Renvoie le message de confirmation."""
        code_livre = self._normaliser(code_livre)
        # On remet le premier exemplaire disponible : le lecteur ne choisit pas
        exemplaire = self.depot.exemplaires_disponibles(code_livre)[0]
        livre = self.depot.trouver_livre(code_livre)

        aujourdhui = date.today()
        emprunt = Emprunt(
            exemplaire.code,
            self._normaliser(matricule),
            aujourdhui,
            regles.calculer_date_limite(aujourdhui),
        )
        numero = self.depot.ajouter_emprunt(emprunt)

        etudiant = self.depot.trouver_etudiant(emprunt.matricule)
        limite = emprunt.date_limite.strftime("%d/%m/%Y")
        lignes = [
            f"Emprunt enregistré. Retour prévu le {limite}.",
            f"Exemplaire à remettre : {exemplaire.code}",
            "",
            f"--- REÇU D'EMPRUNT N° EMP-{numero:04d} ---",
            f"Date : {aujourdhui.strftime('%d/%m/%Y')}",
            f"Étudiant : {etudiant.nom} ({etudiant.matricule})",
            f"Livre : {livre.titre} (exemplaire {exemplaire.code})",
            f"À rendre avant le : {limite}",
        ]
        return "\n".join(lignes)

    # ---------- PAIEMENTS (réutilisés par plusieurs options) ----------

    def encaisser(self, matricule, motif, montant_du, mode, montant_remis=0):
        """Enregistre un paiement. Renvoie (ok, message) : un reçu, ou la raison de l'échec."""
        monnaie = 0
        if mode == config.MODE_ESPECES:
            if montant_remis < montant_du:
                return False, f"Montant insuffisant : {montant_du} FCFA à payer, {montant_remis} FCFA remis."
            monnaie = montant_remis - montant_du

        aujourdhui = date.today()
        numero = self.depot.ajouter_paiement(Paiement(matricule, motif, montant_du, aujourdhui, mode))
        lignes = [
            f"--- REÇU DE PAIEMENT N° REC-{numero:04d} ---",
            f"Date : {aujourdhui.strftime('%d/%m/%Y')}",
            f"Étudiant : {matricule}",
            f"Motif : {motif}",
            f"Mode de paiement : {mode}",
            f"Montant payé : {montant_du} FCFA",
        ]
        if mode == config.MODE_ESPECES:
            lignes.append(f"Montant remis : {montant_remis} FCFA")
            lignes.append(f"Monnaie rendue : {monnaie} FCFA")
        return True, "\n".join(lignes)

    def renouveler_abonnement(self, matricule, montant, mode, montant_remis=0):
        """Renouvelle (ou prolonge) l'abonnement ; `montant` est la part payée. Renvoie (ok, message)."""
        matricule = self._normaliser(matricule)
        etudiant = self.depot.trouver_etudiant(matricule)
        if etudiant is None:
            return False, f"Aucun étudiant avec le matricule {matricule}."
        if not regles.montant_abonnement_valide(montant, etudiant.categorie):
            return False, self._message_montant(etudiant.categorie)

        ok, message = self.encaisser(matricule, "abonnement", montant, mode, montant_remis)
        if ok:
            jours = regles.jours_pour_montant(montant, etudiant.categorie)
            nouvelle_fin = regles.calculer_fin_abonnement(etudiant.fin_abonnement, date.today(), jours)
            self.depot.mettre_a_jour_abonnement(matricule, nouvelle_fin)
            etudiant.fin_abonnement = nouvelle_fin
            chemin = self._enregistrer_carte(etudiant)
            message += (
                f"\nDurée obtenue : {jours} jours"
                f"\nAbonnement valable jusqu'au {nouvelle_fin.strftime('%d/%m/%Y')}."
                f"\nCarte mise à jour : {chemin}"
            )
        return ok, message

    def _message_montant(self, categorie):
        return (
            f"Montant invalide : entre {config.PAIEMENT_MINIMUM_ABONNEMENT} "
            f"et {regles.prix_abonnement(categorie)} FCFA."
        )

    def categorie_de(self, matricule):
        """Catégorie du membre (None si le matricule est inconnu)."""
        etudiant = self.depot.trouver_etudiant(self._normaliser(matricule))
        if etudiant is None:
            return None
        return etudiant.categorie

    def jours_pour_montant(self, categorie, montant):
        return regles.jours_pour_montant(montant, categorie)

    def payer_emprunt_occasionnel(self, matricule, mode, montant_remis=0):
        """Renvoie (ok, message)."""
        matricule = self._normaliser(matricule)
        return self.encaisser(matricule, "emprunt", config.PRIX_EMPRUNT_OCCASIONNEL, mode, montant_remis)

    # ---------- OPTION 5 : ETUDIANTS ET ABONNEMENTS ----------

    def verifier_inscription(self, nom, categorie, telephone, email):
        """Vérifie les informations d'un futur membre. Renvoie (ok, message)."""
        if nom.strip() == "":
            return False, "Le nom ne peut pas être vide."
        if categorie not in config.CATEGORIES_MEMBRES:
            return False, "Catégorie de membre inconnue."
        if not regles.telephone_valide(regles.normaliser_telephone(telephone)):
            return False, "Numéro de téléphone invalide (8 à 15 chiffres)."
        email = email.strip()
        if email != "" and not regles.email_valide(email):
            return False, "Adresse email invalide."
        return True, ""

    def inscrire_etudiant(self, nom, categorie, telephone, email, montant, mode, montant_remis=0):
        """Inscrit un nouveau membre ; `montant` est la part de l'abonnement payée. Renvoie (ok, message)."""
        ok, message = self.verifier_inscription(nom, categorie, telephone, email)
        if not ok:
            return False, message
        if not regles.montant_abonnement_valide(montant, categorie):
            return False, self._message_montant(categorie)

        nom = nom.strip().title()
        telephone = regles.normaliser_telephone(telephone)
        email = email.strip()
        parametres = config.CATEGORIES_MEMBRES[categorie]

        matricule = self.depot.prochain_matricule(parametres["prefixe"])
        # On encaisse d'abord : si le paiement échoue, le membre n'est pas créé
        ok, recu = self.encaisser(matricule, "abonnement", montant, mode, montant_remis)
        if not ok:
            return False, recu

        aujourdhui = date.today()
        jours = regles.jours_pour_montant(montant, categorie)
        fin = regles.calculer_fin_abonnement(aujourdhui, aujourdhui, jours)
        etudiant = Etudiant(matricule, nom, categorie, telephone, email, fin)
        self.depot.ajouter_etudiant(etudiant)
        chemin = self._enregistrer_carte(etudiant)
        return True, (
            f"Inscription réussie : {nom} ({parametres['libelle']}), matricule {matricule}.\n\n"
            f"{recu}\n"
            f"Durée obtenue : {jours} jours\n"
            f"Abonnement valable jusqu'au {fin.strftime('%d/%m/%Y')}.\n"
            f"Carte d'abonnement : {chemin}"
        )

    def prix_abonnement_de(self, matricule):
        """Prix de l'abonnement annuel du membre (0 si le matricule est inconnu)."""
        etudiant = self.depot.trouver_etudiant(self._normaliser(matricule))
        if etudiant is None:
            return 0
        return regles.prix_abonnement(etudiant.categorie)

    def consulter_etudiant(self, matricule):
        """Renvoie (ok, fiche de l'étudiant)."""
        matricule = self._normaliser(matricule)
        etudiant = self.depot.trouver_etudiant(matricule)
        if etudiant is None:
            return False, f"Aucun étudiant avec le matricule {matricule}."

        aujourdhui = date.today()
        fin = etudiant.fin_abonnement.strftime("%d/%m/%Y")
        if regles.abonnement_valide(etudiant.fin_abonnement, aujourdhui):
            abonnement = f"valide jusqu'au {fin}"
        else:
            abonnement = f"EXPIRÉ depuis le {fin}"
        libelle = config.CATEGORIES_MEMBRES[etudiant.categorie]["libelle"]
        email = etudiant.email or "non renseigné"
        lignes = [
            f"Membre : {etudiant.nom} ({etudiant.matricule})",
            f"Catégorie : {libelle}",
            f"Téléphone : {etudiant.telephone}",
            f"Email : {email}",
            f"Abonnement : {abonnement}",
        ]

        emprunts = self.depot.emprunts_en_cours_de(matricule)
        if emprunts:
            lignes.append("Livres empruntés :")
            for emprunt in emprunts:
                exemplaire = self.depot.trouver_exemplaire(emprunt.code_exemplaire)
                livre = self.depot.trouver_livre(exemplaire.code_livre)
                retour = emprunt.date_limite.strftime("%d/%m/%Y")
                note = " (EN RETARD)" if regles.est_en_retard(emprunt, aujourdhui) else ""
                if emprunt.nb_prolongations > 0:
                    note += " (prolongé)"
                lignes.append(f"  - {emprunt.code_exemplaire} {livre.titre}, à rendre le {retour}{note}")
        else:
            lignes.append("Aucun livre emprunté.")

        penalites = self.depot.penalites_impayees(matricule)
        if penalites:
            total = sum(penalite.montant for penalite in penalites)
            lignes.append(f"Pénalités impayées : {total} FCFA")
        else:
            lignes.append("Aucune pénalité impayée.")
        return True, "\n".join(lignes)

    # ---------- OPTION 6 : PAIEMENTS ----------

    def lister_penalites(self, matricule):
        """Renvoie (ok, message). ok vaut False s'il n'y a rien à régler."""
        matricule = self._normaliser(matricule)
        if self.depot.trouver_etudiant(matricule) is None:
            return False, f"Aucun étudiant avec le matricule {matricule}."

        penalites = self.depot.penalites_impayees(matricule)
        if not penalites:
            return False, "Aucune pénalité à régler."

        lignes = ["Pénalités à régler :"]
        for penalite in penalites:
            lignes.append(f"  - {MOTIFS[penalite.motif]} : {penalite.montant} FCFA")
        total = sum(penalite.montant for penalite in penalites)
        lignes.append(f"Total : {total} FCFA")
        return True, "\n".join(lignes)

    def regler_penalites(self, matricule, mode, montant_remis=0):
        """Paie toutes les pénalités impayées de l'étudiant en une fois. Renvoie (ok, message)."""
        matricule = self._normaliser(matricule)
        penalites = self.depot.penalites_impayees(matricule)
        if not penalites:
            return False, "Aucune pénalité à régler."

        total = sum(penalite.montant for penalite in penalites)
        ok, message = self.encaisser(matricule, "penalite", total, mode, montant_remis)
        if ok:
            for penalite in penalites:
                self.depot.marquer_penalite_payee(penalite.id)
            message += "\nToutes les pénalités sont réglées."
        return ok, message

    def historique_paiements(self, matricule):
        """Renvoie (ok, message)."""
        matricule = self._normaliser(matricule)
        if self.depot.trouver_etudiant(matricule) is None:
            return False, f"Aucun étudiant avec le matricule {matricule}."

        paiements = self.depot.paiements_de(matricule)
        if not paiements:
            return True, "Aucun paiement enregistré."
        lignes = ["Historique des paiements :"]
        for paiement in paiements:
            jour = paiement.date.strftime("%d/%m/%Y")
            lignes.append(f"  {jour} - {paiement.motif} - {paiement.montant} FCFA ({paiement.mode})")
        total = sum(paiement.montant for paiement in paiements)
        lignes.append(f"Total payé : {total} FCFA")
        return True, "\n".join(lignes)

    def total_caisse(self):
        return f"Total encaissé par la bibliothèque : {self.depot.total_encaisse()} FCFA"

    # ---------- OPTION 7 : CATALOGUE ----------

    def infos_livre(self, code_livre):
        """Renvoie (ok, texte) : le livre et son nombre d'exemplaires."""
        code_livre = self._normaliser(code_livre)
        livre = self.depot.trouver_livre(code_livre)
        if livre is None:
            return False, f"Aucun livre avec le code {code_livre}."
        nb = len(self.depot.exemplaires_du_livre(code_livre))
        return True, f"{livre.code} {livre.titre} - {livre.auteur} ({nb} exemplaire(s) actuellement)"

    def ajouter_livre(self, titre, auteur, annee, prix, categorie, nb_exemplaires):
        """Ajoute un nouveau livre et ses exemplaires. Renvoie (ok, message)."""
        titre = titre.strip()
        auteur = auteur.strip()
        if titre == "" or auteur == "":
            return False, "Le titre et l'auteur ne peuvent pas être vides."
        if categorie not in config.CATEGORIES:
            return False, "Catégorie inconnue."

        # Un livre déjà au catalogue : on ajoute plutôt des exemplaires
        for existant in self.depot.chercher_livres(titre):
            if existant.titre.lower() == titre.lower() and existant.auteur.lower() == auteur.lower():
                return False, (
                    f"Ce livre existe déjà ({existant.code}). "
                    "Utilisez « Ajouter des exemplaires » pour en ajouter."
                )

        code = self.depot.prochain_code_livre()
        self.depot.ajouter_livre(Livre(code, titre, auteur, annee, prix, categorie))
        codes = self.depot.ajouter_exemplaires(code, nb_exemplaires)
        return True, (
            f"Livre ajouté : {code} « {titre} » ({auteur}), catégorie {categorie}.\n"
            f"Exemplaires créés : {', '.join(codes)}"
        )

    def ajouter_exemplaires(self, code_livre, nombre):
        """Ajoute des exemplaires à un livre existant. Renvoie (ok, message)."""
        code_livre = self._normaliser(code_livre)
        if self.depot.trouver_livre(code_livre) is None:
            return False, f"Aucun livre avec le code {code_livre}."
        codes = self.depot.ajouter_exemplaires(code_livre, nombre)
        return True, f"Exemplaires ajoutés : {', '.join(codes)}"

    # ---------- RAPPELS ET CARTES D'ABONNEMENT ----------

    def lister_expirations_proches(self):
        """Renvoie une liste de tuples (etudiant, jours_restants)."""
        aujourdhui = date.today()
        resultats = []
        for etudiant in self.depot.tous_les_etudiants():
            if regles.abonnement_expire_bientot(etudiant.fin_abonnement, aujourdhui):
                resultats.append((etudiant, (etudiant.fin_abonnement - aujourdhui).days))
        return resultats

    def _texte_carte(self, etudiant):
        largeur = 48
        if regles.abonnement_valide(etudiant.fin_abonnement, date.today()):
            statut = "ACTIVE"
        else:
            statut = "EXPIRÉE"
        libelle = config.CATEGORIES_MEMBRES[etudiant.categorie]["libelle"]
        contenu = [
            "CARTE D'ABONNEMENT".center(largeur),
            "",
            f"Nom : {etudiant.nom}",
            f"N° de carte : {etudiant.matricule}",
            f"Catégorie : {libelle}",
            f"Valide jusqu'au : {etudiant.fin_abonnement.strftime('%d/%m/%Y')}",
            f"Statut : {statut}",
        ]
        lignes = ["+" + "-" * (largeur + 2) + "+"]
        for ligne in contenu:
            lignes.append("| " + ligne.ljust(largeur) + " |")
        lignes.append("+" + "-" * (largeur + 2) + "+")
        return "\n".join(lignes)

    def _enregistrer_carte(self, etudiant):
        """Écrit la carte dans data/cartes/ et renvoie le chemin du fichier."""
        os.makedirs("data/cartes", exist_ok=True)
        chemin = f"data/cartes/{etudiant.matricule}.txt"
        with open(chemin, "w", encoding="utf-8") as fichier:
            fichier.write(self._texte_carte(etudiant) + "\n")
        return chemin

    def afficher_carte(self, matricule):
        """Renvoie (ok, carte) et enregistre la carte dans un fichier texte."""
        matricule = self._normaliser(matricule)
        etudiant = self.depot.trouver_etudiant(matricule)
        if etudiant is None:
            return False, f"Aucun étudiant avec le matricule {matricule}."
        chemin = self._enregistrer_carte(etudiant)
        return True, self._texte_carte(etudiant) + f"\nCarte enregistrée : {chemin}"

    # ---------- OPTION 8 : PROLONGER UN PRÊT ----------

    def prolonger_emprunt(self, code_exemplaire):
        """Prolonge un prêt de 7 jours, avant la date limite. Renvoie (ok, message)."""
        code_exemplaire = self._normaliser(code_exemplaire)
        exemplaire = self.depot.trouver_exemplaire(code_exemplaire)
        if exemplaire is None:
            return False, f"Impossible : aucun exemplaire avec le code {code_exemplaire}."
        livre = self.depot.trouver_livre(exemplaire.code_livre)

        emprunt = self.depot.emprunt_en_cours_de_l_exemplaire(code_exemplaire)
        if emprunt is None or emprunt.date_retour is not None:
            return False, f"L'exemplaire {code_exemplaire} de « {livre.titre} » n'est pas emprunté."

        etudiant = self.depot.trouver_etudiant(emprunt.matricule)
        aujourdhui = date.today()
        raison = regles.raison_de_refus_prolongation(
            emprunt, regles.abonnement_valide(etudiant.fin_abonnement, aujourdhui), aujourdhui
        )
        if raison is not None:
            return False, raison

        nouvelle_limite = regles.calculer_nouvelle_limite(emprunt.date_limite)
        self.depot.prolonger_emprunt(emprunt.id, nouvelle_limite)
        return True, (
            f"Prêt prolongé : « {livre.titre} » (exemplaire {code_exemplaire}), "
            f"{etudiant.nom} ({etudiant.matricule}).\n"
            f"Nouvelle date limite : {nouvelle_limite.strftime('%d/%m/%Y')}."
        )

    # ---------- OPTION 9 : LECTURE SUR PLACE ----------

    def commencer_lecture(self, code_livre):
        """Réserve un exemplaire pour une lecture sur place. Renvoie (ok, message)."""
        code_livre = self._normaliser(code_livre)
        livre = self.depot.trouver_livre(code_livre)
        if livre is None:
            return False, f"Impossible : aucun livre avec le code {code_livre}."
        disponibles = self.depot.exemplaires_disponibles(code_livre)
        if not disponibles:
            return False, f"Impossible : Le livre « {livre.titre} » n'a plus d'exemplaire disponible."

        exemplaire = disponibles[0]
        self.depot.ajouter_lecture(exemplaire.code, date.today())
        return True, (
            f"Lecture sur place enregistrée : « {livre.titre} ».\n"
            f"Exemplaire à remettre au lecteur : {exemplaire.code}\n"
            "À remettre en rayon après la lecture (menu Lecture sur place)."
        )

    def terminer_lecture(self, code_exemplaire):
        """Remet un exemplaire en rayon. Renvoie (ok, message)."""
        code_exemplaire = self._normaliser(code_exemplaire)
        if self.depot.lecture_en_cours_de(code_exemplaire) is None:
            return False, f"L'exemplaire {code_exemplaire} n'est pas en lecture sur place."
        self.depot.terminer_lecture(code_exemplaire, date.today())
        return True, f"Exemplaire {code_exemplaire} remis en rayon : il est de nouveau disponible."

    def lister_lectures(self):
        """Renvoie une liste de tuples (code_exemplaire, titre)."""
        resultats = []
        for lecture in self.depot.lectures_en_cours():
            exemplaire = self.depot.trouver_exemplaire(lecture.code_exemplaire)
            livre = self.depot.trouver_livre(exemplaire.code_livre)
            resultats.append((lecture.code_exemplaire, livre.titre))
        return resultats
