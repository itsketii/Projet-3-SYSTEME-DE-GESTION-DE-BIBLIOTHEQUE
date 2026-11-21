from datetime import date

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

    def _demander_montant_abonnement(self, categorie):
        """Demande la part de l'abonnement à payer et affiche la durée obtenue."""
        prix = config.CATEGORIES_MEMBRES[categorie]["prix_abonnement"]
        minimum = config.PAIEMENT_MINIMUM_ABONNEMENT
        print(f"Abonnement d'un an : {prix} FCFA (paiement partiel possible, minimum {minimum} FCFA)")
        montant = self._demander_entier(f"Montant à payer (entre {minimum} et {prix} FCFA) : ", minimum, prix)
        jours = self.controleur.jours_pour_montant(categorie, montant)
        print(f"{montant} FCFA = {jours} jours d'abonnement")
        return montant

    # ---------- MENU PRINCIPAL ----------

    def lancer(self):
        print("=== BIBLIOTHÈQUE UNIVERSITAIRE ===")
        nb_retards = len(self.controleur.lister_retards())
        if nb_retards > 0:
            print(f"Attention : {nb_retards} emprunt(s) en retard.")
        nb_expirations = len(self.controleur.lister_expirations_proches())
        if nb_expirations > 0:
            print(f"Rappel : {nb_expirations} abonnement(s) expirent dans les {config.RAPPEL_EXPIRATION_JOURS} jours.")

        while True:
            print("\n--- MENU PRINCIPAL ---")
            print("1. Rechercher un livre")
            print("2. Emprunter un livre")
            print("3. Rendre un livre")
            print("4. Consulter les retards")
            print("5. Étudiants et abonnements")
            print("6. Paiements")
            print("7. Catalogue (ajouter des livres)")
            print("8. Prolonger un prêt")
            print("9. Lecture sur place")
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
            elif choix == "7":
                self.catalogue()
            elif choix == "8":
                self.prolonger()
            elif choix == "9":
                self.lecture()
            elif choix == "0":
                print("Au revoir !")
                break
            else:
                print("Choix invalide.")

    # ---------- OPTION 1 : RECHERCHER UN LIVRE ----------

    def rechercher(self):
        mot_cle = self._demander("Mot-clé (titre ou auteur, Entrée pour tout voir) : ")

        print("Filtrer par type de livre :")
        print("  0. Tous les types")
        for numero, categorie in enumerate(config.CATEGORIES, start=1):
            print(f"  {numero}. {categorie}")
        choix = self._demander_entier("Votre choix : ", 0, len(config.CATEGORIES))
        categorie = None
        if choix > 0:
            categorie = config.CATEGORIES[choix - 1]

        resultats = self.controleur.rechercher_livres(mot_cle, categorie)
        if not resultats:
            print("Aucun livre trouvé.")
            return
        print()
        for livre, nb_exemplaires, disponibles in resultats:
            if disponibles:
                statut = f"{len(disponibles)}/{nb_exemplaires} disponible(s) : {', '.join(disponibles)}"
            else:
                statut = f"aucun exemplaire disponible (0/{nb_exemplaires})"
            print(f"{livre.code} {livre.titre} - {livre.auteur} ({livre.annee}) [{livre.categorie}]")
            print(f"      {statut}")

    # ---------- OPTION 4 : CONSULTER LES RETARDS ----------

    def retards(self):
        liste = self.controleur.lister_retards()
        if not liste:
            print("Aucun emprunt en retard.")
            return
        print("--- EMPRUNTS EN RETARD ---")
        for code_exemplaire, livre, etudiant, date_limite, jours, montant in liste:
            limite = date_limite.strftime("%d/%m/%Y")
            print(
                f"{code_exemplaire} {livre.titre} | {etudiant.nom} ({etudiant.matricule}) "
                f"| prévu le {limite} | {jours} jour(s) | {montant} FCFA"
            )
            email = etudiant.email or "pas d'email"
            print(f"      Contact : {etudiant.telephone} / {email}")

    # ---------- OPTION 2 : EMPRUNTER UN LIVRE ----------

    def emprunter(self):
        code = self._demander("Code du livre (ex : L002) : ")
        matricule = self._demander("Matricule de l'étudiant : ")

        statut, message = self.controleur.verifier_emprunt(code, matricule)
        if statut == "refus":
            print(message)
            return

        if statut == "abonnement_expire":
            print(message)
            prix = self.controleur.prix_abonnement_de(matricule)
            print(f"  1. Renouveler l'abonnement (jusqu'à {prix} FCFA)")
            print(f"  2. Payer cet emprunt à l'unité ({config.PRIX_EMPRUNT_OCCASIONNEL} FCFA)")
            print("  0. Annuler")
            choix = self._demander_entier("Votre choix : ", 0, 2)
            if choix == 0:
                print("Emprunt annulé.")
                return

            if choix == 1:
                categorie = self.controleur.categorie_de(matricule)
                montant = self._demander_montant_abonnement(categorie)
                mode, montant_remis = self._demander_paiement()
                ok, recu = self.controleur.renouveler_abonnement(matricule, montant, mode, montant_remis)
            else:
                mode, montant_remis = self._demander_paiement()
                ok, recu = self.controleur.payer_emprunt_occasionnel(matricule, mode, montant_remis)
            print("\n" + recu)
            if not ok:
                return

        print("\n" + self.controleur.enregistrer_emprunt(code, matricule))

    # ---------- OPTION 3 : RENDRE UN LIVRE ----------

    def rendre(self):
        code = self._demander("Code de l'exemplaire rendu (ex : L002-01) : ")
        print("État du livre :")
        print("  1. Bon état")
        print("  2. Abîmé")
        print("  3. Perdu ou détruit")
        choix = self._demander_entier("Votre choix : ", 1, 3)
        etat = ["bon", "abime", "perdu"][choix - 1]

        ok, message = self.controleur.rendre_livre(code, etat)
        print("\n" + message)

    # ---------- OPTION 5 : ETUDIANTS ET ABONNEMENTS ----------

    def etudiants(self):
        while True:
            print("\n--- ÉTUDIANTS ET ABONNEMENTS ---")
            print("1. Inscrire un nouveau membre")
            print("2. Consulter la fiche d'un membre")
            print("3. Renouveler un abonnement")
            print("4. Abonnements qui expirent bientôt")
            print("5. Afficher la carte d'un membre")
            print("0. Retour")
            choix = self._demander_entier("Votre choix : ", 0, 5)

            if choix == 1:
                self._inscrire()
            elif choix == 2:
                self._consulter()
            elif choix == 3:
                self._renouveler()
            elif choix == 4:
                self._expirations()
            elif choix == 5:
                self._carte()
            else:
                return

    def _inscrire(self):
        nom = self._demander("Nom complet : ")

        print("Catégorie de membre :")
        cles = list(config.CATEGORIES_MEMBRES)
        for numero, cle in enumerate(cles, start=1):
            parametres = config.CATEGORIES_MEMBRES[cle]
            print(f"  {numero}. {parametres['libelle']} ({parametres['prix_abonnement']} FCFA par an)")
        choix = self._demander_entier("Votre choix : ", 1, len(cles))
        categorie = cles[choix - 1]

        telephone = self._demander("Téléphone : ")
        email = self._demander("Email (Entrée pour passer) : ")

        ok, message = self.controleur.verifier_inscription(nom, categorie, telephone, email)
        if not ok:
            print(message)
            return

        montant = self._demander_montant_abonnement(categorie)
        mode, montant_remis = self._demander_paiement()
        ok, message = self.controleur.inscrire_etudiant(
            nom, categorie, telephone, email, montant, mode, montant_remis
        )
        print("\n" + message)

    def _consulter(self):
        matricule = self._demander("Matricule de l'étudiant : ")
        ok, fiche = self.controleur.consulter_etudiant(matricule)
        print("\n" + fiche)

    def _renouveler(self):
        matricule = self._demander("Matricule de l'étudiant : ")
        ok, fiche = self.controleur.consulter_etudiant(matricule)
        print("\n" + fiche)
        if not ok:
            return

        print()
        categorie = self.controleur.categorie_de(matricule)
        montant = self._demander_montant_abonnement(categorie)
        mode, montant_remis = self._demander_paiement()
        ok, message = self.controleur.renouveler_abonnement(matricule, montant, mode, montant_remis)
        print("\n" + message)

    def _expirations(self):
        liste = self.controleur.lister_expirations_proches()
        if not liste:
            print(f"Aucun abonnement n'expire dans les {config.RAPPEL_EXPIRATION_JOURS} jours.")
            return
        print(f"--- ABONNEMENTS QUI EXPIRENT DANS LES {config.RAPPEL_EXPIRATION_JOURS} JOURS ---")
        for etudiant, jours in liste:
            fin = etudiant.fin_abonnement.strftime("%d/%m/%Y")
            email = etudiant.email or "pas d'email"
            print(f"{etudiant.matricule} {etudiant.nom} | expire le {fin} (dans {jours} jour(s))")
            print(f"      Contact : {etudiant.telephone} / {email}")

    def _carte(self):
        matricule = self._demander("Matricule de l'étudiant : ")
        ok, carte = self.controleur.afficher_carte(matricule)
        print("\n" + carte)

    # ---------- OPTION 6 : PAIEMENTS ----------

    def paiements(self):
        while True:
            print("\n--- PAIEMENTS ---")
            print("1. Régler les pénalités d'un étudiant")
            print("2. Historique des paiements d'un étudiant")
            print("3. Caisse (total encaissé)")
            print("0. Retour")
            choix = self._demander_entier("Votre choix : ", 0, 3)

            if choix == 1:
                self._regler_penalites()
            elif choix == 2:
                self._historique()
            elif choix == 3:
                print("\n" + self.controleur.total_caisse())
            else:
                return

    def _regler_penalites(self):
        matricule = self._demander("Matricule de l'étudiant : ")
        ok, liste = self.controleur.lister_penalites(matricule)
        print("\n" + liste)
        if not ok:
            return

        mode, montant_remis = self._demander_paiement()
        ok, message = self.controleur.regler_penalites(matricule, mode, montant_remis)
        print("\n" + message)

    def _historique(self):
        matricule = self._demander("Matricule de l'étudiant : ")
        ok, texte = self.controleur.historique_paiements(matricule)
        print("\n" + texte)

    # ---------- OPTION 7 : CATALOGUE ----------

    def catalogue(self):
        while True:
            print("\n--- CATALOGUE ---")
            print("1. Ajouter un nouveau livre")
            print("2. Ajouter des exemplaires à un livre")
            print("0. Retour")
            choix = self._demander_entier("Votre choix : ", 0, 2)

            if choix == 1:
                self._ajouter_livre()
            elif choix == 2:
                self._ajouter_exemplaires()
            else:
                return

    def _ajouter_livre(self):
        titre = self._demander("Titre : ")
        auteur = self._demander("Auteur : ")
        if titre == "" or auteur == "":
            print("Le titre et l'auteur ne peuvent pas être vides.")
            return
        annee = self._demander_entier("Année de parution : ", 1, date.today().year)
        prix = self._demander_entier("Prix du livre (FCFA) : ", 1, 1000000)

        print("Catégorie :")
        for numero, categorie in enumerate(config.CATEGORIES, start=1):
            print(f"  {numero}. {categorie}")
        choix = self._demander_entier("Votre choix : ", 1, len(config.CATEGORIES))
        categorie = config.CATEGORIES[choix - 1]

        nombre = self._demander_entier("Nombre d'exemplaires : ", 1, 20)
        ok, message = self.controleur.ajouter_livre(titre, auteur, annee, prix, categorie, nombre)
        print("\n" + message)

    def _ajouter_exemplaires(self):
        code = self._demander("Code du livre (ex : L002) : ")
        ok, infos = self.controleur.infos_livre(code)
        print(infos)
        if not ok:
            return
        nombre = self._demander_entier("Nombre d'exemplaires à ajouter : ", 1, 20)
        ok, message = self.controleur.ajouter_exemplaires(code, nombre)
        print("\n" + message)

    # ---------- OPTION 8 : PROLONGER UN PRÊT ----------

    def prolonger(self):
        code = self._demander("Code de l'exemplaire à prolonger (ex : L002-01) : ")
        ok, message = self.controleur.prolonger_emprunt(code)
        print("\n" + message)

    # ---------- OPTION 9 : LECTURE SUR PLACE ----------

    def lecture(self):
        while True:
            print("\n--- LECTURE SUR PLACE ---")
            print("1. Commencer une lecture (le lecteur choisit un livre)")
            print("2. Remettre un exemplaire en rayon")
            print("3. Lectures en cours")
            print("0. Retour")
            choix = self._demander_entier("Votre choix : ", 0, 3)

            if choix == 1:
                code = self._demander("Code du livre (ex : L002) : ")
                ok, message = self.controleur.commencer_lecture(code)
                print("\n" + message)
            elif choix == 2:
                code = self._demander("Code de l'exemplaire (ex : L002-01) : ")
                ok, message = self.controleur.terminer_lecture(code)
                print("\n" + message)
            elif choix == 3:
                liste = self.controleur.lister_lectures()
                if not liste:
                    print("Aucune lecture en cours.")
                for code_exemplaire, titre in liste:
                    print(f"{code_exemplaire} {titre}")
            else:
                return
