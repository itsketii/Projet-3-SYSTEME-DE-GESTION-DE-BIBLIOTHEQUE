from app.controllers.controleur_bibliotheque import ControleurBibliotheque
from app.models.depot_sqlite import DepotSQLite
from app.views.vue_console import VueConsole


def main():
    depot = DepotSQLite("data/bibliotheque.db")
    controleur = ControleurBibliotheque(depot)
    vue = VueConsole(controleur)
    vue.lancer()


if __name__ == "__main__":
    main()