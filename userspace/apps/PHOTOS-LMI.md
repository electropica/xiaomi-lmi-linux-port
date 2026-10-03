# Photos (Koko) sur Xiaomi lmi

Koko 25.04.0-1 ne chargeait pas son interface : SQLite, Wayland et deux modules
QML étaient absents dans l'installation sans recommandations. La recette
scripts/install.sh les déclare maintenant explicitement.

Le helper files/lmi-photos utilise le rendu Qt Quick logiciel, uniquement pour
Koko. Il contourne les erreurs GPU observées au démarrage ; le contrôle distant
charge l'interface mais la confirmation visuelle reste en attente. Deux warnings
QML de placement/empilement restent présents. Ce helper expérimental n'est pas
installé automatiquement par la recette générique.

Le téléphone d'essai utilise une surcharge utilisateur org.kde.koko.desktop
qui conserve les traductions du lanceur système et appelle /usr/local/bin/lmi-photos.
Retirer cette surcharge rétablit le lanceur système, sans changer les paquets GPU.

Voir [checklist et observations](../../docs/validation/lmi-app-checklist-2026-10-03.md).
