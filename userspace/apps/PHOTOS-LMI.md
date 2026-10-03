# Photos (Koko) sur Xiaomi lmi

## État validé le 3 octobre 2026

L'opérateur confirme l'ouverture de l'image de test, le retour à la galerie
et l'absence de clavier après les corrections. Une capture distante montre la
miniature visible sans sélection. Les helpers sont installés sur le téléphone
et ajoutés à la recette des applications ; aucun nouveau build n'a été lancé.

Le lanceur active le mode mobile Kirigami, le thème Breeze et QT_IM_MODULE=compose
uniquement pour Photos. Le clavier virtuel de recherche/saisie reste à tester :
ce choix évite l'activation Wayland indésirable et ne corrige pas le clavier
des autres applications. Avec le runtime GPU lmi présent, il utilise Zink/RHI,
testé à environ 67 Mo de mémoire de scope. Sans ce runtime, il revient au rendu
Qt Quick logiciel, dont les icônes de navigation restent imparfaites.

## Miniatures : diagnostic et contournement

Koko utilise les aperçus KIO. Sur ce kernel, shmget échoue avec ENOSYS. Dans
KIO 6.13.0, la lecture de l'en-tête dimensions/format du flux n'a lieu que
si la mémoire partagée est disponible. Le producteur kio-extras 25.04.3 écrit
cet en-tête également en mode sans mémoire partagée : les sources révèlent
une incompatibilité de ce chemin de repli. Une trace a aussi révélé un arrêt
du worker hors écran sur « Could not initialize GLX » ; QT_QPA_OFFSCREEN_NO_GLX=1
supprime ce besoin pour les workers de Photos.

Le helper lmi-photos-thumbnails prépare des PNG de 256 pixels dans le cache
standard utilisateur, avec URI, date et taille de l'image originale. KIO lit
ces aperçus : affichage confirmé par capture. Le générateur gdk-pixbuf est
limité en mémoire, et le lot à trois secondes/256 entrées examinées par
lancement. Les images originales ne sont pas modifiées. Les aperçus valides
sont réutilisés ; les fichiers non pris en charge sont ignorés sans bloquer
le lancement. Le répertoire Images défini par XDG et les chemins passés au
lanceur sont concernés. Une grande galerie ou des images ajoutées pendant
la session peuvent nécessiter une relance. Les vidéos ne sont pas couvertes
par ce contournement.

Les dépendances Qt/QML, SQLite, SVG, Breeze, KIO et gdk-pixbuf sont explicites
dans scripts/install.sh. Le lanceur local conserve les traductions du fichier
desktop système. Les helpers et la surcharge utilisateur du téléphone sont
des réparations userspace, pas la validation d'une nouvelle image.

## Limites ouvertes

Le bandeau de dossier « Images » placé au-dessus des onglets du bas, les
libellés tronqués et certaines icônes restent à améliorer. Le zoom Koko est
borné jusqu'à ×100, sans nouvelle limite spécifique au téléphone. Suppression,
édition, recherche, grandes galeries et vidéos n'ont pas été validées. Photos
est une visionneuse, pas une validation de la caméra.

Sources : [KIO Debian 6.13.0-6](https://sources.debian.org/src/kf6-kio/6.13.0-6/src/gui/previewjob.cpp/),
[kio-extras Debian 25.04.3](https://sources.debian.org/src/kio-extras/4%3A25.04.3-1/thumbnail/thumbnail.cpp/),
[mode mobile Kirigami](https://develop.kde.org/hig/layout_and_nav/).
Voir la [checklist](../../docs/validation/lmi-app-checklist-2026-10-03.md).
