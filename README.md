
# Système de gestion de bibliothèque

Application **console** en Python pour gérer une bibliothèque universitaire : recherche de livres, emprunts, retours, suivi des retards, abonnements des étudiants, pénalités et paiements (espèces, carte, mobile money).

Le projet suit l'architecture **MVC** (Modèle - Vue - Contrôleur) et n'utilise que la bibliothèque standard de Python : **aucune installation de paquet n'est nécessaire**.

## Lancer le programme

```
python main.py
```

Python 3.9 ou plus est requis. Au premier lancement, la base SQLite `data/bibliotheque.db` est créée automatiquement, avec des livres et des étudiants de démonstration.

## Menu

```
1. Rechercher un livre
2. Emprunter un livre
3. Rendre un livre
4. Consulter les retards
5. Étudiants et abonnements (inscrire, consulter, renouveler)
6. Paiements (régler les pénalités, historique, caisse)
0. Quitter
```

Chaque emprunt, retour et paiement produit un **reçu numéroté** (EMP-0001, RET-0001, REC-0001).

## Règles de la bibliothèque

Tous les réglages se trouvent dans `config.py`.

| Règle                           | Valeur                                                              |
| -------------------------------- | ------------------------------------------------------------------- |
| Durée d'un emprunt              | 14 jours                                                            |
| Livres empruntés en même temps | 3 maximum par étudiant                                             |
| Pénalité de retard             | 200 FCFA par jour, plafonnée au prix du livre                      |
| Livre rendu abîmé              | 30 % du prix du livre                                               |
| Livre perdu ou détruit          | 100 % du prix du livre (aucune pénalité de retard en plus)        |
| Abonnement                       | 5 000 FCFA pour 1 an                                                |
| Emprunt sans abonnement valide   | 500 FCFA par livre                                                  |
| Modes de paiement                | Espèces, carte bancaire, Wave, Orange Money, MTN Money, Moov Money |

Un étudiant qui a des pénalités impayées ne peut pas emprunter. Un livre perdu n'est plus disponible.

## Architecture

```
.
├── main.py                              # point d'entrée
├── config.py                            # réglages (durées, tarifs, modes de paiement)
├── app/
│   ├── models/
│   │   ├── entites.py                   # Livre, Etudiant, Emprunt, Penalite, Paiement
│   │   ├── regles.py                    # règles métier (retards, pénalités, abonnement)
│   │   └── depot_sqlite.py              # accès à la base SQLite
│   ├── controllers/
│   │   └── controleur_bibliotheque.py   # orchestre les règles et le dépôt
│   └── views/
│       └── vue_console.py               # menus et saisies dans le terminal
└── data/                                # base SQLite générée (ignorée par Git)
```

- **Modèle** : les données (`entites.py`), les règles (`regles.py`) et la persistance (`depot_sqlite.py`).
- **Contrôleur** : décide quoi faire en appelant les règles et le dépôt, sans jamais afficher ni lire au clavier.
- **Vue** : affiche et lit les saisies, sans aucune règle métier.

## Organisation Git

Une branche par fonctionnalité (`feature/entites`, `feature/base`, `feature/regles`, `feature/service`, `feature/menu`, `feature/ci`), fusionnée dans `main` par Pull Request relue. Une intégration continue (GitHub Actions) vérifie que le code est valide et que le programme démarre.
