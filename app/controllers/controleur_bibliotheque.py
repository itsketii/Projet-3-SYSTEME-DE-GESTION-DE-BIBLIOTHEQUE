from datetime import date

import config
from app.models import regles
from app.models.entites import Emprunt, Paiement


class ControleurBibliotheque:
    """Relie la vue (console), les règles et le dépôt (base de données)."""

    def __init__(self, depot):
        self.depot = depot

    def _normaliser(self, texte):
        return texte.strip().upper()

    # ---------- OPTION 1 : RECHERCHER UN LIVRE ----------

    def rechercher_livres(self, mot_cle):
        """Renvoie une liste de tuples (livre, disponible)."""
        resultats = []
        for livre in self.depot.chercher_livres(mot_cle):
            emprunt = self.depot.emprunt_en_cours_du_livre(livre.code)
            disponible = emprunt is None
            resultats.append((livre, disponible))
        return resultats

    # ---------- OPTION 4 : CONSULTER LES RETARDS ----------

    def lister_retards(self):
        """Renvoie une liste de tuples (livre, etudiant, date_limite, jours, montant)."""
        aujourdhui = date.today()
        retards = []
        for emprunt in self.depot.tous_les_emprunts_en_cours():
            if regles.est_en_retard(emprunt, aujourdhui):
                livre = self.depot.trouver_livre(emprunt.code_livre)
                etudiant = self.depot.trouver_etudiant(emprunt.matricule)
                jours = regles.jours_de_retard(emprunt.date_limite, aujourdhui)
                montant = regles.penalite_retard(jours, livre.prix)
                retards.append((livre, etudiant, emprunt.date_limite, jours, montant))
        return retards

        # ---------- OPTION 2 : EMPRUNTER UN LIVRE ----------

    def verifier_emprunt(self, code_livre, matricule):
        """Renvoie (statut, message). Statut : "refus", "paiement_requis" ou "ok"."""
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
            self.depot.emprunt_en_cours_du_livre(code_livre),
            len(self.depot.emprunts_en_cours_de(matricule)),
            len(self.depot.penalites_impayees(matricule)) > 0,
        )
        if raison is not None:
            return "refus", raison

        if not regles.abonnement_valide(etudiant.fin_abonnement, date.today()):
            fin = etudiant.fin_abonnement.strftime("%d/%m/%Y")
            return "paiement_requis", f"Abonnement expiré depuis le {fin}."
        return "ok", ""

    def enregistrer_emprunt(self, code_livre, matricule):
        """Crée l'emprunt (à appeler après verifier_emprunt). Renvoie le message de confirmation."""
        aujourdhui = date.today()
        emprunt = Emprunt(
            self._normaliser(code_livre),
            self._normaliser(matricule),
            aujourdhui,
            regles.calculer_date_limite(aujourdhui),
        )
        self.depot.ajouter_emprunt(emprunt)
        return f"Emprunt enregistré. Retour prévu le {emprunt.date_limite.strftime('%d/%m/%Y')}."

    # ---------- PAIEMENTS (réutilisés par plusieurs options) ----------

    def encaisser(self, matricule, motif, montant_du, montant_remis):
        """Enregistre un paiement. Renvoie (ok, message) : un reçu, ou la raison de l'échec."""
        if montant_remis < montant_du:
            return False, f"Montant insuffisant : {montant_du} FCFA à payer, {montant_remis} FCFA remis."

        aujourdhui = date.today()
        self.depot.ajouter_paiement(Paiement(matricule, motif, montant_du, aujourdhui))
        monnaie = montant_remis - montant_du
        recu = (
            "--- REÇU ---\n"
            f"Date : {aujourdhui.strftime('%d/%m/%Y')}\n"
            f"Étudiant : {matricule}\n"
            f"Motif : {motif}\n"
            f"Montant payé : {montant_du} FCFA\n"
            f"Monnaie rendue : {monnaie} FCFA"
        )
        return True, recu

    def renouveler_abonnement(self, matricule, montant_remis):
        """Renvoie (ok, message)."""
        matricule = self._normaliser(matricule)
        ok, message = self.encaisser(matricule, "abonnement", config.PRIX_ABONNEMENT, montant_remis)
        if ok:
            etudiant = self.depot.trouver_etudiant(matricule)
            nouvelle_fin = regles.calculer_fin_abonnement(etudiant.fin_abonnement, date.today())
            self.depot.mettre_a_jour_abonnement(matricule, nouvelle_fin)
            message += f"\nAbonnement valable jusqu'au {nouvelle_fin.strftime('%d/%m/%Y')}."
        return ok, message

    def payer_emprunt_occasionnel(self, matricule, montant_remis):
        """Renvoie (ok, message)."""
        matricule = self._normaliser(matricule)
        return self.encaisser(matricule, "emprunt", config.PRIX_EMPRUNT_OCCASIONNEL, montant_remis)