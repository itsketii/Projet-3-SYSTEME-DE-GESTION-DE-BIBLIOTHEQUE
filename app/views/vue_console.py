import config


class VueConsole:
    """Interface console : affiche les menus et lit les saisies.
    Aucune règle métier ici : tout est confié au contrôleur."""

    def __init__(self, controleur):
        self.controleur = controleur

    # ---------- OUTILS ----------

    def _demander(self, question):
        return input(question).strip()

    def _demander_entier(self, question, minimum, maximum):
        """Redemande tant que la réponse n'est pas un nombre entre minimum et maximum."""
        while True:
            texte = self._demander(question)
            if texte.isdigit() and minimum <= int(texte) <= maximum:
                return int(texte)
            print(f"Veuillez entrer un nombre entre {minimum} et {maximum}.")

    def _demander_paiement(self):
        """Demande le mode de paiement. Renvoie (mode, montant_remis)."""
        print("Mode de paiement :")
        for numero, mode in enumerate(config.MODES_PAIEMENT, start=1):
            print(f"  {numero}. {mode}")
        choix = self._demander_entier("Votre choix : ", 1, len(config.MODES_PAIEMENT))
        mode = config.MODES_PAIEMENT[choix - 1]

        montant_remis = 0
        if mode == config.MODE_ESPECES:
            montant_remis = self._demander_entier("Montant remis (FCFA) : ", 0, 10000000)
        return mode, montant_remis

    # ---------- MENU PRINCIPAL ----------

    def lancer(self):
        print("=== BIBLIOTHÈQUE UNIVERSITAIRE ===")
        nb_retards = len(self.controleur.lister_retards())
        if nb_retards > 0:
            print(f"Attention : {nb_retards} emprunt(s) en retard.")

        while True:
            print("\n--- MENU PRINCIPAL ---")
            print("1. Rechercher un livre")
            print("2. Emprunter un livre")
            print("3. Rendre un livre")
            print("4. Consulter les retards")
            print("5. Étudiants et abonnements")
            print("6. Paiements")
            print("0. Quitter")
            choix = self._demander("Votre choix : ")

            if choix == "1":
                self.rechercher()
            elif choix == "2":
                self.emprunter()
            elif choix == "3":
                self.rendre()
            elif choix == "4":
                self.retards()
            elif choix == "5":
                self.etudiants()
            elif choix == "6":
                self.paiements()
            elif choix == "0":
                print("Au revoir !")
                break
            else:
                print("Choix invalide.")

    def rechercher(self):
        mot_cle = self._demander("Mot-clé (titre ou auteur) : ")
        resultats = self.controleur.rechercher_livres(mot_cle)

        if not resultats:
            print("Aucun livre trouvé.")
            return

        for livre, disponible in resultats:
            statut = "Disponible" if disponible else "Indisponible"
            print(
                f"{livre.code} - {livre.titre} - "
                f"{livre.auteur} ({livre.annee}) [{statut}]"
            )

    def retards(self):
        retards = self.controleur.lister_retards()

        if not retards:
            print("Aucun emprunt en retard.")
            return

        print("--- EMPRUNTS EN RETARD ---")
        for livre, etudiant, date_limite, jours, montant in retards:
            limite = date_limite.strftime("%d/%m/%Y")
            print(
                f"{livre.code} - {livre.titre} | "
                f"{etudiant.nom} ({etudiant.matricule}) | "
                f"{jours} jour(s) de retard | "
                f"{montant} FCFA | Retour prévu le {limite}"
            )