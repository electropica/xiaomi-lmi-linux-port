# Checklist des applications lmi — 3 octobre 2026

Chaque application est testée seule. Un démarrage réussi ne valide pas toutes
ses fonctions. Les confirmations antérieures au redémarrage sont séparées
des contrôles du démarrage actuel. Aucun compte, message ou contact personnel
n'est créé pour ces essais. Les actions visuelles attendent la confirmation
de l'opérateur, sans délai imposé pour effectuer son geste.

| Application | Fonctionnement global | Fonctionnement des menus | Traduction |
|---|---|---|---|
| Discussions (Chatty) | Ouverture et relance confirmées après contournement ; limite réelle de 384 Mio, zéro swap et aucun nouvel OOM dans le contrôle du scope. SMS/MMS non validés, aucun modem détecté. | Défaut signalé : fenêtre « Raccourcis » trop grande/impossible à réduire ; fermeture et adaptation encore à valider. | Paramètres encore en anglais malgré locale française ; catalogue partiel. Correction locale préparée mais non validée, priorité basse. |
| Calculatrice | Démarrage obtenu ; calcul non confirmé. Clavier apparaît à la saisie sans bouton visible pour le cacher ; application fermée par l'opérateur. | À tester après résolution du clavier. | À tester. |
| Fichiers | Navigation et noms chinois confirmés avant redémarrage ; à recontrôler. | À tester. | À tester ; affichage des noms chinois validé, distinct de la langue des menus. |
| Éditeur de texte | Saisie, création/enregistrement, réouverture, modification/enregistrement et fermeture normale validés à distance sur fichiers de test. Dialogue Enregistrer sous utilisable au toucher confirmé par l’opérateur avec le lanceur final. | Enregistrer sous via le menu réel crée un fichier distinct au contenu identique ; sélecteur GNOME adapté à l’écran. Autres menus restent à tester. | Préférences françaises déjà signalées par l’opérateur ; traduction non prioritaire. |
| Papiers | À tester : PDF, changement de page et recherche. | À tester. | À tester. |
| Photos (Koko) | Image de test ouverte et zoomée par l’opérateur ; miniature visible sur capture après contournement du cache KIO. Aucune capture caméra validée. | Retour à la galerie fonctionnel et clavier caché confirmés après correction. Menu coulissant accessible ; bandeau Images et libellés encore mal adaptés. Recherche/édition/vidéo non validées. | Libellés français visibles ; couverture complète non validée. |
| Horloges | À tester : chronomètre/minuterie ; son dépend du rétablissement audio. | À tester. | À tester. |
| Agenda | À tester : affichage/navigation ; ne pas créer d'événement personnel. | À tester. | À tester. |
| Contacts | À tester : affichage/navigation ; ne pas modifier les contacts personnels. | À tester. | À tester. |
| Paramètres | À tester : navigation/affichage ; éviter les changements de réseau/alimentation durant les autres essais. | À tester. | À tester. |
| Console | À tester : ouverture et commande inoffensive. | À tester. | À tester. |
| Lampe torche lmi | Allumer/éteindre confirmés avant redémarrage ; à recontrôler. | Pas de menu supplémentaire testé. | Interface française présente ; pas de validation multilingue. |
| Amberol | MP3 et volume confirmés avant redémarrage ; aucune carte ALSA détectée après redémarrage. | À tester. | À tester. |
| Showtime | MP4 confirmé avant redémarrage ; son à rétablir. | À tester. | À tester. |
| Enregistreur | À tester ; microphone non validé. | À tester. | À tester. |
| Megapixels | Bloqué : pipeline de capture standard non établi. | Non validé. | Non prioritaire avant capture fonctionnelle. |
| Appels | À tester ; aucun modem détecté, aucun appel réel lancé. | À tester. | À tester. |
| Web | À tester ; DNS Internet défaillant lors du dernier contrôle. | À tester. | À tester. |
| Cartes | À tester ; réseau et position non validés. | À tester. | À tester. |
| Météo | À tester ; réseau requis pour l'actualisation. | À tester. | À tester. |
| Geary | À tester ; aucun compte à configurer ni courriel à envoyer durant l'essai. | À tester. | À tester. |

### Contrôles système séparés

- Heure incorrecte signalée par l'opérateur. Lecture du téléphone :
  `2026-10-02T13:42:19+00:00`, fuseau `Etc/UTC`, `NTPSynchronized=no`, alors
  que la date opérateur est le 3 octobre 2026 en Europe/Paris. Vérifier à la
  fois l'horloge/synchronisation et le fuseau ; ne pas attribuer tout le
  décalage au seul fuseau. Aucun réglage d'heure modifié dans ce contrôle.
- Clavier : apparition à la saisie sans moyen visible de le masquer.
  `sm.puri.OSK0.SetVisible(false)` fonctionne par SSH, mais cela ne valide
  pas un geste ou bouton utilisable depuis l'interface. Problème ouvert.

Priorité décidée par l'opérateur : fonctionnement global, puis menus,
puis traduction. Une seule application active dans le protocole d'essai ;
laisser le temps de confirmer chaque geste. L'essai courant est l’Éditeur de texte ; les résultats Chatty et Photos restent conservés.

## Ordre de validation

Terminer l'essai isolé de Chatty et conserver son diagnostic, puis passer à
Calculatrice, Fichiers, Éditeur de texte, Papiers et Photos. Ensuite vérifier
les utilitaires, la lampe et les applications multimédia. Les fonctions
caméra, modem et Internet restent explicitement bloquées tant que leurs
prérequis matériels ou réseau ne sont pas disponibles.

## Incident Chatty

Version installée : 0.8.7-2. Le journal kernel du démarrage précédent indique
un anonymous RSS de 6 438 704 kB avant la mise à mort du processus. Le bus de
session a également subi un OOM ; le téléphone a redémarré pendant l'incident.
Le diagnostic n'a pas envoyé de SMS ni modifié les données utilisateur.

La trace GDB avec arrêt sur la première erreur critique passe par le
fournisseur video4linux2, le fournisseur uvch264, le moniteur de périphériques
GStreamer et libpurple. Abaisser les rangs des fournisseurs n'a pas suffi.
Une vue de plugins isolée excluant `libgstvideo4linux2.so` et
`libgstuvch264.so`, avec un registre séparé, permet au processus de rester
actif lors du contrôle initial. Cela désigne la détection vidéo comme piste
causale du démarrage, sans établir encore l'erreur exacte du pilote/kernel.
Les paquets GStreamer globaux sont conservés. La messagerie et le modem ne
sont pas validés par la simple ouverture de l'interface.

Le redémarrage a interrompu le suivi batterie temporaire de six heures :
aucun résultat d'autonomie complète n'est acquis. Le correctif CPU et UPower
sont actifs ; la carte ALSA n'est plus détectée sur ce démarrage.


## Reprise après une relance ordinaire

L'opérateur a fermé l'essai isolé puis rouvert Discussions avec le lanceur
ordinaire, qui n'avait pas encore reçu le contournement. La consommation a
de nouveau bloqué la session. Chatty a été tué par SSH dès son retour ; la
mémoire disponible est remontée à environ 7 Go. Le lanceur aurait dû être
sécurisé avant la vérification manuelle ; cet essai ne constitue pas un
échec du filtrage isolé mais confirme que le chemin de lancement ordinaire
restait dangereux.

Le helper `userspace/apps/files/lmi-chatty-safe` a ensuite été installé
localement sous `/usr/local/bin/lmi-chatty-safe`. Une vue de plugins par
symlinks exclut seulement video4linux2 et uvch264, avec un registre privé.
Les lanceurs desktop et D-Bus de l'utilisateur pointent désormais vers ce
helper. Il demande un scope systemd utilisateur avec MemoryMax=384 MiB,
MemorySwapMax=0 et TasksMax=128, sans repli non limité. Ces changements ne
sont pas activés dans le constructeur d'image générique.

L'installation a été vérifiée par lecture des deux commandes Exec. La délégation mémoire utilisateur a été vérifiée après redémarrage : un
scope inoffensif a exposé memory.max=402653184 et memory.swap.max=0. Les deux
overrides et le helper étaient toujours présents. Aucune application n’a été
lancée pour ce contrôle. Le lancement normal et la navigation restent à vérifier avant de marquer Discussions OK.
La validation des 20 autres applications n'a pas été effectuée pendant ce
lot. Les essais sont arrêtés pour préserver le quota annoncé par l'opérateur.

Après une mise à jour des plugins GStreamer, les liens de cette vue isolée
devront être revus. Pour rollback, retirer seulement les deux overrides
utilisateur créés et le helper/vue installés ; les fichiers et plugins
système originaux n'ont pas été modifiés. Un rollback réexpose le défaut
initial : ne pas relancer Chatty sans confinement dans cet état.


## Reprise ciblée : lanceur habituel de Discussions

Le lanceur utilisateur protégé a été testé. L'opérateur a confirmé le menu,
la fermeture et la relance sans blocage. Le processus relancé appartenait à
un scope utilisateur exposant memory.max=402653184, memory.swap.max=0,
memory.current=71299072 et zéro événement oom/oom_kill lors du contrôle.
Cette validation corrige les points de lancement/délégation encore en attente
dans les relevés antérieurs ; elle ne valide pas les fonctions SMS/MMS.

Une correction française de la seule ressource de paramètres a été générée
localement depuis Chatty 0.8.7-2. Elle ne modifie pas le paquet système et n'est
pas une validation visuelle ni une modification du constructeur générique.
L'opérateur a demandé de reporter la traduction au profit du fonctionnement.

SSH Windows a atteint le serveur mais refusé la lecture de la clé privée
dans WSL et du fichier de clés d'hôte. L'accès WSL existant reste utilisé ;
aucune clé privée n'a été copiée et aucune vérification d'hôte désactivée.


## Règle de comparaison batterie — Wi-Fi et essais d'interface

L'opérateur précise que les références batterie actuelles ont été prises
sans connexion Wi-Fi, avec la radio désactivée pour certains essais.
Ne pas mélanger une future mesure avec Wi-Fi connecté à ces références.
Consigner séparément : radio activée/désactivée, association Wi-Fi effective,
écran, USB, musique/lampe et correctif CPU. « Non associé » n'est pas
équivalent à « radio désactivée ». Les comparaisons historiques détaillées
conservent leurs états Wi-Fi respectifs ; aucune n'est requalifiée ici.

Pour les tests d'applications, un inhibiteur temporaire idle+suspend lié à
USB online a été lancé, limité à deux heures et libéré lorsque l'USB passe
hors ligne. Il ne change pas les préférences persistantes. Arrêter ce service
avant une nouvelle mesure batterie : l'écran forcé et le collecteur de
surveillance USB font partie des conditions d'essai à maîtriser. L'activation
branchée a été vérifiée ; le débranchement de cette inhibition n'a pas été
testé physiquement dans ce lot. Aucun nouveau test batterie n'a été effectué.


## Correction manuelle de l'heure — 3 octobre 2026

L'horloge système a été réglée depuis l'UTC du PC et le fuseau installé est
Europe/Paris. Lecture vérifiée : 2026-10-03T09:55:19+02:00. timedatectl a
refusé l'autorisation ; les fichiers localtime/timezone et date ont été
réglés directement par root. Aucun redémarrage ni écriture RTC effectué.
La synchronisation NTP automatique et le maintien de l'heure après un
redémarrage restent à vérifier. Ce résultat remplace le statut « heure
incorrecte » pour le démarrage courant, pas pour les observations antérieures.


## Retour manuel du 3 octobre — après correction de l'heure

Ces résultats viennent de l'opérateur. « OK » ne valide pas une fonction
matérielle non explicitement essayée. Priorité : fonctionnement global,
menus, puis traduction ; une application à la fois.

| Application | Fonctionnement global | Fonctionnement des menus | Traduction |
|---|---|---|---|
| Éditeur de texte | Fermeture impossible signalée, puis disparition après plusieurs minutes ; crash non confirmé. | Enregistrer/Enregistrer sous débordent de l'écran. Préférences accessibles. | Préférences françaises confirmées. |
| Appels | Interface OK ; appel et modem non validés. | Pas de défaut rapporté. | Non évaluée séparément. |
| Discussions | Fonctionnement confirmé après contournement du blocage. | Raccourcis trop grands, retour impossible. | Préférences partiellement françaises ; correction complète reportée. |
| Contacts | OK selon l'opérateur. | Pas de défaut rapporté. | Non évaluée séparément. |
| Amberol | Lecture auparavant validée ; pas de nouvelle mesure audio ici. | Raccourcis clavier inadaptés. | Non évaluée séparément. |
| Console, Fichiers, Papiers | OK selon l'opérateur. | Pas de défaut rapporté. | Non évaluée séparément. |
| Geary | Ouverture OK ; aucun compte, réception/envoi non testés. | À approfondir. | Non évaluée séparément. |
| Horloges | OK selon l'opérateur ; alarme matérielle non explicitement validée. | Pas de défaut rapporté. | Non évaluée séparément. |
| Megapixels | Chargement puis fenêtre vide ; capture non fonctionnelle. | Non validés. | Secondaire. |
| Photos (Koko) | Fenêtre vide. | Non validés. | Secondaire. |
| Paramètres | Réouvre la dernière page au lieu de la page principale. | Certaines options paraissent limitées ; revue complète encore requise. | Non évaluée séparément. |

### Défauts transversaux et essais restant à faire

- Aperçu des applications ouvertes : rayures noires et blanches ; cause non établie.
- Dialogues Raccourcis clavier : débordement et absence de retour, sur plusieurs applications.
  Ils restent utiles avec un clavier externe, mais doivent pouvoir être fermés sur téléphone.
- Grille d'applications : débordement/gestes de défilement à vérifier visuellement.
- Libellé du filtre mobile tronqué. Le réglage actuel est app-filter-mode=['adaptive'],
  force-adaptive=[] ; déclaration mobile et compatibilité réelle sont distinctes.
- Enregistreur : microphone et écouteur interne non testés ; ne pas les confondre avec le HP inférieur.
- Rotation automatique, GPS et boussole non validés.
- Galerie photo/vidéo et capture caméra sont deux fonctions distinctes ; Showtime lit les vidéos,
  Koko doit encore fonctionner et Megapixels n'a pas de pipeline de capture établi.
- Clavier logiciel : absence de bouton visible de réduction toujours ouverte.

### Contrôles à distance de cette reprise

Koko 25.04.0-1 signale un plugin Qt Wayland absent, un pilote SQL QSQLITE absent,
puis l'échec de chargement de Main.qml : module org.kde.kquickcontrolsaddons absent.
Cela établit des dépendances manquantes, sans prouver que tous les défauts graphiques
seront résolus par leur installation. La recette utilise --no-install-recommends.

L'éditeur 48.3-3 a journalisé des erreurs de dimensions GtkLabel et des annulations
de dialogue. Aucun OOM/segfault n'a été retrouvé dans le contrôle ciblé de ce démarrage ;
la disparition de sa fenêtre reste inexpliquée.

Les trois périphériques IIO exposés sont des ADC PM8150/PM8150B/PM8150L, pas des
accéléromètres ou magnétomètres. iio-sensor-proxy n'est pas installé ; aucun capteur
de rotation standard n'est actuellement établi. GeoClue est installé, ce qui ne
prouve ni la présence d'un récepteur GPS utilisable ni une localisation satellite.

### Batterie et protocole pendant l'absence

Téléphone débranché vers 10h40 puis rebranché. Lecture après reconnexion à 11h58 :
96 %, charge_counter=2753852 µAh, Charging. Faute de valeur de départ synchronisée,
ce seul relevé ne permet pas de calculer la consommation de l'intervalle.
Le service CPU idle est actif. L'inhibiteur temporaire d'écran branché est actif ;
il devra être arrêté avant tout nouveau protocole batterie comparatif.
L'opérateur est absent : aucun débranchement, écoute ou validation visuelle ne
doit être demandé ni supposé. Aucun changement Wi-Fi pour les essais batterie.


## Photos : dépendances et essai limité — 3 octobre 2026

La recette d'applications explicite maintenant qt6-wayland, libqt6sql6-sqlite,
qml6-module-org-kde-kquickcontrolsaddons et qml6-module-org-kde-purpose.
Ces quatre paquets, avec leurs dépendances (29 nouveaux paquets au total), ont
été installés sur le téléphone sans mise à jour générale. dpkg --audit est vide.
Les erreurs QSQLITE, plugin Wayland et modules QML manquants ont disparu.

Le démarrage accéléré a ensuite montré des erreurs Mesa get-param/pipe allocation
et egl: failed to create dri2 screen. Un essai QT_QUICK_BACKEND=software limité
à Koko a chargé l'interface sans ces erreurs dans le relevé de démarrage, à environ
69 Mio dans le cgroup. Deux avertissements QML de placement/empilement persistent.
Le service de test avait MemoryMax=512 Mio et RuntimeMaxSec=20 : aucun processus
de test illimité n'est conservé. Cela valide le chargement automatique, pas le
rendu visuel, la navigation, le zoom ou la lecture de vidéos.

Le helper userspace/apps/files/lmi-photos et une surcharge utilisateur du lanceur
Photos appliquent le rendu logiciel seulement à Koko sur le téléphone d'essai.
Le helper n'est pas activé par défaut dans le constructeur générique avant
validation visuelle. Les dépendances explicites, elles, sont intégrées à la recette.
Retour arrière local : retirer la surcharge utilisateur org.kde.koko.desktop ;
le lanceur système demeure intact. Le rendu logiciel pourrait coûter plus de CPU
pendant l'affichage d'images ; consommation non mesurée.

Paramètres mémorise last-panel='privacy' dans org.gnome.Settings. L'aide de la
version installée n'expose pas d'option --overview ; remettre la clé à vide
sélectionnerait le premier panneau, sans garantir un accueil principal.
Aucun faux correctif de lanceur n'a donc été appliqué. La navigation mobile
vers la liste des panneaux reste à vérifier visuellement.

Références techniques :
- [Qt : rendu logiciel Qt Quick](https://doc.qt.io/qt-6.5/qtquick-visualcanvas-adaptations.html).
- [GNOME Settings 48 : restauration du dernier panneau](https://sources.debian.org/src/gnome-control-center/1:48.4-1~deb13u1/shell/cc-window.c/).

### Installation d'applications et options matérielles

La liste d'applications n'est pas fixe : les paquets Debian ARM64 sont installables
avec APT. Firefox s'appelle firefox-esr dans Debian trixie ; aucune installation
Firefox n'a été faite dans cet essai. GNOME Software fournit un catalogue graphique
avec les moteurs appropriés, mais n'est pas installé ici. Architecture ARM64 et
interface adaptée au téléphone sont deux critères distincts.

« Souris et pavé tactile » concerne les périphériques de pointage, notamment
externes ; ce panneau n'est pas le réglage du tactile de l'écran ou du clavier
virtuel. Des panneaux dépendent des périphériques et services présents. Leur
présence limitée ne démontre pas à elle seule un défaut d'affichage.

La rotation automatique et une boussole exigent des capteurs exposés et leur
prise en charge logicielle ; les ADC observés ne les remplacent pas. Cartes peut
utiliser GeoClue, mais une position réseau ne constituerait pas une validation GPS.

Références : [Firefox ESR Debian](https://packages.debian.org/trixie/firefox-esr),
[GNOME Software](https://apps.gnome.org/Software/).


Capture distante : grim a été installé comme outil de diagnostic (84 ko installés).
La capture fonctionne, mais montre l'écran verrouillé ; aucun secret ni réglage
de verrouillage n'a été modifié. Les captures restent privées, hors Git.
La confirmation visuelle de Photos et des autres menus reste donc en attente.


## Photos : retour opérateur et navigation — 3 octobre 2026

L'opérateur confirme que l'interface fonctionne, avec un menu accessible par
glissement. Une image de test PNG a été envoyée au téléphone, hors Git.
L'image s'affiche. En revanche, impossible de revenir à la galerie et clavier
visible pendant la consultation. Le zoom/dézoom paraît sans limites.

Le clavier a été masqué ponctuellement par l'API OSK ; ce geste distant ne
constitue pas une correction générale du clavier. Le helper Photos active
maintenant QT_QUICK_CONTROLS_MOBILE=1, seulement pour Koko. qt6-svg-plugins,
absent, a été installé et ajouté à la recette : une icône vidéo apparaît sur
la capture après installation, mais tous les boutons ne sont pas encore validés.
Confirmation ultérieure : le Retour fonctionne et le clavier reste caché après ouverture d'image, avec le helper final.

La source officielle Koko v25.04.0 BaseImageDelegate.qml définit minimumZoomSize=8
et maximumZoomFactor=100 : la plage est très large, pas réellement infinie.
Ces bornes n'ont pas été modifiées. Une restriction adaptée au téléphone reste
à décider après rétablissement de la navigation.

Références : [mode mobile Kirigami](https://develop.kde.org/hig/layout_and_nav/),
[bornes de zoom Koko](https://github.com/KDE/koko/blob/v25.04.0/src/qml/imagedelegate/BaseImageDelegate.qml).


### Photos : miniatures et lanceur final

Le défaut de galerie transparente est contourné par génération automatique
du cache standard de miniatures. Une capture sans sélection montre l'image de
test. Le test sur téléphone valide le redimensionnement 256 pixels, les champs
URI/date/taille du PNG et la réutilisation sans réécriture du cache inchangé.
L'opérateur confirme ensuite : « Retour fonctionne, clavier caché ».

Le helper emploie le runtime Zink lmi lorsqu'il est présent, le mode mobile,
Breeze, compose pour l'entrée et un worker hors écran sans GLX. Les trois
moteurs précédemment essayés ne suffisaient pas à rétablir la génération KIO.
Une trace shmget=ENOSYS et les sources des versions installées étayent
l'incompatibilité du flux d'aperçu en l'absence de mémoire partagée.
Le contournement couvre les images du dossier XDG et les fichiers passés au
lanceur, avec limites de temps/mémoire ; il ne couvre pas les vidéos.

La ligne « Images » près du bas est le bandeau de navigation du dossier défini
par AlbumView ; sa disposition et les onglets tronqués restent ouverts. Les
bornes du zoom n'ont pas été modifiées. Voir [Photos lmi](../../userspace/apps/PHOTOS-LMI.md)
pour le diagnostic, les sources et les limites. Captures et image de test sont
hors Git. Le maintien temporaire de l'écran actif sur USB reste réservé aux
tests d'interface et doit être arrêté avant toute mesure de batterie.


## Éditeur de texte : enregistrement et fermeture — 3 octobre 2026

Versions testées : gnome-text-editor 48.3-3, nautilus 48.3-2,
xdg-desktop-portal 1.20.3+ds-1 et backend GNOME 48.0-2.
Le dialogue GTK initial dépasse la largeur de l'écran ; le bouton Enregistrer
est hors écran. Ce défaut empêche un parcours tactile normal. Les touches
distantes seules ne suffisaient pas à tester tous les boutons ; un périphérique
tactile uinput temporaire a permis de toucher les contrôles visibles, puis
était détruit après chaque geste. wtype est un outil de test, pas une nouvelle
dépendance du build. Aucun document personnel n'a été édité.

Le routage FileChooser utilise maintenant GNOME pour Phosh, en conservant les
autres préférences du portail. Le lanceur local de l'Éditeur force les portails
GTK4 et transmet l'environnement Wayland au bus d'activation. Avant cette
transmission, Nautilus activé par D-Bus ne pouvait pas connecter son affichage,
avec une erreur org.gnome.Mutter.ServiceChannel ; après, il démarre et fournit
le sélecteur adapté. Le défaut ne demandait ni nouveau kernel ni nouveau rootfs.

Contrôles réellement passés : création de deux lignes par saisie dans l'Éditeur,
enregistrement par le bouton visible et vérification du contenu sur disque ;
fermeture normale de la fenêtre puis réouverture avec texte visible ; menu
Enregistrer sous produisant un second fichier identique ; ajout d'une troisième
ligne et sauvegarde dans ce fichier ; nouvelle fermeture avec disparition du
processus. Ce parcours valide des fonctions, pas seulement un lancement.

Le helper et le fichier de routage sont installés sur le téléphone ; la recette
et le staging du constructeur préparent leur intégration au prochain build.
Les fichiers desktop gardent leurs traductions et dirigent aussi l'action
Nouvelle fenêtre vers le helper. Aucun build lourd n'a été lancé. Confirmation
tactile obtenue : l’opérateur a ouvert Enregistrer sous puis annulé et confirme
le dialogue utilisable, avec le bouton de validation visible. Le clavier reste
visible dans l'Éditeur en mode saisie : son masquage général n'est pas corrigé
par ce lot. Les portails pour applications sandboxées ne sont pas validés ;
le document portal FUSE reste en échec sur le kernel courant.

Source : [GNOME 47 et ses nouveaux dialogues de fichiers](https://release.gnome.org/47/).
