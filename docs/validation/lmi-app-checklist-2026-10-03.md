# Checklist des applications lmi — 3 octobre 2026

Chaque application est testée seule. Un démarrage réussi ne valide pas toutes
ses fonctions. Les confirmations antérieures au redémarrage sont séparées
des contrôles du démarrage actuel. Aucun compte, message ou contact personnel
n'est créé pour ces essais. Les actions visuelles attendent la confirmation
de l'opérateur, sans délai imposé pour effectuer son geste.

| Application | Fonction principale à vérifier | État connu |
|---|---|---|
| Discussions (Chatty) | Démarrage, navigation ; SMS séparément | Échec initial : 6,4 Go, OOM et perte de session. Reproduit sous limite 384 Mo. Essai avec plugins vidéo filtrés actif à environ 108 Mo ; confirmation visuelle en attente. Aucun modem détecté. |
| Calculatrice | Calcul simple, effacement | À tester |
| Fichiers | Navigation, ouverture, noms chinois | Confirmé avant redémarrage ; à recontrôler |
| Éditeur de texte | Ouvrir, modifier et enregistrer un fichier de test | À tester |
| Papiers | Ouvrir un PDF, changer de page, rechercher | À tester |
| Photos (Koko) | Ouvrir et zoomer sur une image | À tester ; ce n'est pas l'application de capture |
| Horloges | Chronomètre et minuterie | À tester ; avertissement sonore dépend du rétablissement audio |
| Agenda | Affichage et navigation entre dates | À tester ; création éventuelle d'un événement de test séparée |
| Contacts | Affichage et navigation | À tester ; ne pas modifier les contacts personnels |
| Paramètres | Navigation, affichage des réglages | À tester ; ne pas modifier le réseau ou l'alimentation pendant les autres essais |
| Console | Ouverture et commande inoffensive | À tester |
| Lampe torche lmi | Allumer puis éteindre visiblement | Boutons confirmés avant redémarrage ; à recontrôler |
| Amberol | Lecture MP3, pause, reprise, volume | Lecture MP3 et boutons volume confirmés avant redémarrage ; plus de carte son détectée après redémarrage |
| Showtime | Lecture MP4, pause, recherche dans la vidéo, audio | Lecture MP4 confirmée avant redémarrage ; audio à rétablir |
| Enregistreur | Capture et relecture d'un enregistrement court | À tester ; microphone non validé |
| Megapixels | Aperçu et prise de photo | Bloqué : pipeline de capture standard non établi |
| Appels | Démarrage ; appel séparément | À tester ; aucun modem détecté, ne pas lancer d'appel réel |
| Web | Démarrage, page locale ; navigation Internet séparément | À tester ; DNS Internet actuellement défaillant |
| Cartes | Démarrage, affichage d'une carte | À tester ; données réseau et position non validées |
| Météo | Démarrage, affichage des informations | À tester ; requiert réseau pour actualiser les données |
| Geary | Démarrage, navigation | À tester ; ne pas configurer un compte ni envoyer de courriel |

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
