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
| Éditeur de texte | À tester : ouvrir, modifier, enregistrer un fichier de test. | À tester. | À tester. |
| Papiers | À tester : PDF, changement de page et recherche. | À tester. | À tester. |
| Photos (Koko) | À tester : afficher et zoomer une image ; ce n'est pas la capture caméra. | À tester. | À tester. |
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
laisser le temps de confirmer chaque geste. L'essai courant reste Discussions.

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
