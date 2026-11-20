from datetime import date

from app.models import regles


class ControleurBibliotheque:
    """Relie la vue (console), les règles et le dépôt (base de données)."""

    def __init__(self, depot):
        self.depot = depot

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