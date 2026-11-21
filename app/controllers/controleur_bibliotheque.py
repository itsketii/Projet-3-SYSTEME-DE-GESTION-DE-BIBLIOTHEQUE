from datetime import date

import config
from app.models import regles
from app.models.entites import Emprunt, Etudiant, Paiement, Penalite

ETATS = {"bon": "Bon état", "abime": "Abîmé", "perdu": "Perdu ou détruit"}
MOTIFS = {"retard": "Retard", "abime": "Livre abîmé", "perdu": "Livre perdu ou détruit"}


class ControleurBibliotheque:
    """Relie la vue (console), les règles et le dépôt (base de données)."""

    def __init__(self, depot):
        self.depot = depot

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

    def renouveler_abonnement(self, matricule, mode, montant_remis=0):
        """Renvoie (ok, message)."""
        matricule = self._normaliser(matricule)
        etudiant = self.depot.trouver_etudiant(matricule)
        if etudiant is None:
            return False, f"Aucun étudiant avec le matricule {matricule}."

        ok, message = self.encaisser(matricule, "abonnement", config.PRIX_ABONNEMENT, mode, montant_remis)
        if ok:
            nouvelle_fin = regles.calculer_fin_abonnement(etudiant.fin_abonnement, date.today())
            self.depot.mettre_a_jour_abonnement(matricule, nouvelle_fin)
            message += f"\nAbonnement valable jusqu'au {nouvelle_fin.strftime('%d/%m/%Y')}."
        return ok, message

    def payer_emprunt_occasionnel(self, matricule, mode, montant_remis=0):
        """Renvoie (ok, message)."""
        matricule = self._normaliser(matricule)
        return self.encaisser(matricule, "emprunt", config.PRIX_EMPRUNT_OCCASIONNEL, mode, montant_remis)

    # ---------- OPTION 5 : ETUDIANTS ET ABONNEMENTS ----------

    def inscrire_etudiant(self, nom, mode, montant_remis=0):
        """Inscrit un nouvel étudiant (premier abonnement payé). Renvoie (ok, message)."""
        nom = nom.strip().title()
        if nom == "":
            return False, "Le nom ne peut pas être vide."

        matricule = self.depot.prochain_matricule()
        # On encaisse d'abord : si le paiement échoue, l'étudiant n'est pas créé
        ok, recu = self.encaisser(matricule, "abonnement", config.PRIX_ABONNEMENT, mode, montant_remis)
        if not ok:
            return False, recu

        aujourdhui = date.today()
        fin = regles.calculer_fin_abonnement(aujourdhui, aujourdhui)
        self.depot.ajouter_etudiant(Etudiant(matricule, nom, fin))
        return True, (
            f"Inscription réussie : {nom}, matricule {matricule}.\n\n"
            f"{recu}\n"
            f"Abonnement valable jusqu'au {fin.strftime('%d/%m/%Y')}."
        )

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
        lignes = [
            f"Étudiant : {etudiant.nom} ({etudiant.matricule})",
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