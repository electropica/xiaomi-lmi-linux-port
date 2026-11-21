# Garde CPU : alerte sans arrêt de processus

Le téléphone utilise une variante du garde MiniMax qui journalise une charge
soutenue, sans arrêter d'application. L'ancien exécutable reste en place sur
l'appareil ; une surcharge systemd lance `lmi-cpu-alert.py` à sa place.

La recette locale v4 a été adaptée pour installer ce comportement sous son
nom de garde initial. La recette v4 complète n'est pas présente dans ce dépôt.
Cette alerte n'est pas une mesure de consommation et ne démontre pas qu'une
application est défectueuse. Le seuil et les événements sont dans le journal
systemd. La syntaxe Python et l'absence d'appel à `stop_process` dans la boucle
ont été vérifiées ; un essai de surcharge sur appareil reste à faire.
