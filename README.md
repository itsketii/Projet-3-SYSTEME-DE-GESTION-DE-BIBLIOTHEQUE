# Projet-4-SYSTEME-DE-GESTION-DE-BIBLIOTHEQUE

Application **console** en Python pour gérer une bibliothèque ouverte à tous (élèves, étudiants, personnes extérieures) : catalogue avec exemplaires, emprunts, retours, prolongations, lecture sur place, abonnements avec cartes, pénalités et paiements (espèces, carte, mobile money).

Le projet suit l'architecture **MVC** (Modèle - Vue - Contrôleur) et n'utilise que la bibliothèque standard de Python : **aucune installation de paquet n'est nécessaire**.

## Installation et lancement

### 1. Prérequis

- **Python 3.9 ou plus** (vérifier avec `python --version`)
- **Git** (pour récupérer le projet)

### 2. Récupérer le projet

```
git clone https://github.com/itsketii/Projet-3-SYSTEME-DE-GESTION-DE-BIBLIOTHEQUE.git
cd Projet-3-SYSTEME-DE-GESTION-DE-BIBLIOTHEQUE
```

### 3. (Facultatif) Créer un environnement virtuel

```
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux / macOS
```

### 4. Lancer le programme

```
python main.py
```

Au premier lancement, la base SQLite `data/bibliotheque.db` est créée automatiquement, avec un catalogue de démonstration (24 titres, 43 exemplaires) et 5 membres. Pour repartir de zéro, supprimer ce fichier.

## Menu

```
1. Rechercher un livre (par mot-clé et/ou par type)
2. Emprunter un livre
3. Rendre un livre
4. Consulter les retards
5. Étudiants et abonnements (inscrire, fiche, renouveler, rappels, carte)
6. Paiements (régler les pénalités, historique, caisse)
7. Catalogue (ajouter des livres et des exemplaires)
8. Prolonger un prêt
9. Lecture sur place
0. Quitter
```

Chaque emprunt, retour et paiement produit un **reçu numéroté** (EMP-0001, RET-0001, REC-0001). Le reçu d'emprunt rappelle les frais payés quand l'emprunt est réglé à l'unité. Les cartes d'abonnement sont enregistrées dans `data/cartes/`.

## Règles de la bibliothèque

Tous les réglages se trouvent dans `config.py`.

| Règle                           | Valeur                                                                                                                             |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Abonnement annuel                | Élève 2 000 FCFA, étudiant 3 000 FCFA, personne extérieure 5 000 FCFA                                                          |
| Paiement partiel de l'abonnement | à partir de 1 000 FCFA, durée proportionnelle au montant (au prorata de 365 jours)                                               |
| Rappel d'expiration              | 7 jours avant la fin de l'abonnement                                                                                               |
| Emprunt sans abonnement valide   | 500 FCFA par livre                                                                                                                 |
| Durée d'un emprunt              | 14 jours                                                                                                                           |
| Livres empruntés en même temps | 3 maximum par membre                                                                                                               |
| Prolongation                     | 7 jours, une seule fois, à demander avant la date limite                                                                          |
| Pénalité de retard             | 200 FCFA par jour, plafonnée au prix du livre                                                                                     |
| Livre rendu abîmé              | 30 % du prix du livre                                                                                                              |
| Livre perdu ou détruit          | 100 % du prix du livre (aucune pénalité de retard en plus)                                                                       |
| Suspension                       | après 3 livres abîmés ou perdus, l'abonnement est annulé : le membre doit régler ses pénalités et renouveler                |
| Lecture sur place                | sans identification du lecteur ; l'exemplaire est occupé jusqu'à sa remise en rayon (clôturée automatiquement le jour suivant) |
| Modes de paiement                | Espèces, carte bancaire, Wave, Orange Money, MTN Money, Moov Money                                                                |

- Un livre peut avoir **plusieurs exemplaires** (L002-01, L002-02…). Le lecteur demande un livre, et le programme indique l'exemplaire à lui remettre.
- Un membre qui a des pénalités impayées ne peut pas emprunter. Un exemplaire perdu n'est plus disponible.
- Chaque membre a un téléphone (obligatoire) et un email (facultatif) : ils s'affichent dans la liste des retards et des abonnements qui expirent.

## Architecture

```
.
├── main.py                              # point d'entrée
├── config.py                            # réglages (durées, tarifs, catégories, modes de paiement)
├── app/
│   ├── models/
│   │   ├── entites.py                   # Livre, Exemplaire, Etudiant, Emprunt, Penalite, Paiement, Lecture
│   │   ├── regles.py                    # règles métier (retards, pénalités, abonnements, prolongation)
│   │   └── depot_sqlite.py              # accès à la base SQLite
│   ├── controllers/
│   │   └── controleur_bibliotheque.py   # orchestre les règles et le dépôt
│   └── views/
│       └── vue_console.py               # menus et saisies dans le terminal
└── data/                                # base SQLite et cartes générées (ignorées par Git)
```

- **Modèle** : les données (`entites.py`), les règles (`regles.py`) et la persistance (`depot_sqlite.py`).
- **Contrôleur** : décide quoi faire en appelant les règles et le dépôt, sans jamais afficher ni lire au clavier.
- **Vue** : affiche et lit les saisies, sans aucune règle métier.

## Organisation Git

Une branche par fonctionnalité (`feature/entites`, `feature/base`, `feature/regles`, `feature/service`, `feature/menu`, `feature/ci`, `feature/categories`, `feature/catalogue`, `feature/membres`, `feature/abonnements`…), fusionnée dans `main` par Pull Request relue. Une intégration continue (GitHub Actions) vérifie que le code est valide et que le programme démarre.
