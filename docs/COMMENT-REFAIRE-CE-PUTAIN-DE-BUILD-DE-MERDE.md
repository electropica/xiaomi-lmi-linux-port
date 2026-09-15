# Refaire le build Xiaomi lmi / Mobian — recette, preuves et limites

**État consolidé : 15 septembre 2026.**

Ce document doit rester utilisable si les conversations ChatGPT/Codex disparaissent. Il sépare strictement :

1. **PROCÉDURE ACTUELLE RECOMMANDÉE** — ce que le dépôt actuel sait faire et ce qui est réellement exécutable ;
2. **RECONSTRUCTION AVEC ARTEFACTS HISTORIQUES CONSERVÉS** — ce qui permet de reconstruire M0 sans refaire toute la closure ;
3. **RECONSTRUCTION DE ZÉRO** — ce qui exige encore des entrées historiques manquantes ;
4. **HISTORIQUE / ARCHÉOLOGIE** — preuves utiles, mais pas méthode actuelle.

Les mots **PROUVÉ / TRÈS PROBABLE / INCONNU** sont normatifs. Une voie marquée non validée ne doit pas être présentée comme le build de référence.

---

## Réponse courte à la question « peut-on refaire demain le build validé sans les conversations ? »

**PAS ENCORE À 100 %.**

**PROUVÉ** — Le dépôt actuel contient le builder M1 et le tree M0 DISPLAY historique survit. Le golden D-repro-01 exact survit également. La géométrie 4K, l'assemblage M0, la fabrication M1, les validations hôte et les identités du build `archi-validation-01` sont suffisamment documentés.

**ÉTAT ACTUEL** — Le garde-fou historique fondé sur le SHA global du préflight `b12eeb3c...` a été remplacé localement par un contrôle de la taille du BASE_RAW et du SHA-256 de tout le préfixe réellement hérité avant `pmOS_root` (255 852 544 octets). Le golden D-repro-01 passe ce contrôle. Après agrandissement et passage par `expand-gpt-4k.py`, ce préfixe devient bit-à-bit identique à celui du M1 validé `archi-validation-01`. **Le garde-fou est validé hors build ; le build complet puis la validation téléphone restent à effectuer.**

Donc il existe aujourd'hui :
- une **ancienne voie historiquement validée** dont le préflight BASE_RAW exact manque ;
- une **voie actuelle utilisant le golden D-repro-01 comme enveloppe**, dont l'admission M1 est préparée et validée hors build, mais dont le build complet et le test téléphone restent à valider.

---

# A. PROCÉDURE ACTUELLE RECOMMANDÉE

## A1. Entrées à conserver impérativement

### Dépôt actif

`/home/linuxagent/ProjetMobian`

Entrées logiques du builder :
- `build.sh`
- `phosh/scripts/build-m1-phosh.sh`
- `phosh/scripts/expand-gpt-4k.py`
- `apps/scripts/install.sh`
- `debug/scripts/install.sh` — **préparé mais pas encore validé par un build**
- couches `gpu/`, `wifi/`, `bluetooth/`, `display/` utilisées par le builder.

### M0_TREE actuellement disponible

`/home/linuxagent/ProjetMobian-ancien-workspace/Mobian-M0/rootfs-m0-display-work`

**PROUVÉ** — Le package-set installé du tree correspond exactement aux 330 triplets paquet/version/architecture du manifeste historique. Les contrôles historiques `dpkg-audit`, états non installés et diff de package-set sont propres. Les fichiers critiques USB réseau, SSH, `authorized_keys` et `kernel.release` correspondent aux références conservées.

### Golden récupéré

`/home/linuxagent/D-repro-01-userdata-rootfs-ssh-key-weston-post-clear-v2.img`

- taille : `1490026496`
- SHA-256 : `4ec785b85d48494847b81e6a02a74486725affe7707bd3de2dd466d91206be11`

**PROUVÉ** — Il fournit l'enveloppe disque historique : GPT 4K, `pmOS_boot` et octets hors `pmOS_root`.

### BASE_RAW historiquement accepté par M1 — MANQUANT

Nom : `Mobian-M0-userdata-rootfs-330-display-preflight.img`

- taille : `1490026496`
- SHA-256 : `b12eeb3c561a37e84f2a99037587fdf833979a3b6f4610a03d4e820a51ae6399`

**PROUVÉ** — C'est l'entrée utilisée par le build `archi-validation-01`.

**PROUVÉ** — Cette image n'est plus présente dans les emplacements locaux recherchés et sa suppression de l'ancien emplacement est documentée.

## A2. Contrat du builder actuel

`build.sh` reçoit :

`BASE_RAW M0_TREE [NAME]`

puis lance le builder M1 dans le namespace utilisateur/montage attendu.

**PROUVÉ** — `BASE_RAW` et `M0_TREE` sont indépendants :
- le BASE_RAW fournit l'enveloppe disque héritée ;
- le M0_TREE est copié comme point de départ du nouveau système M1 ;
- l'ancienne `pmOS_root` du BASE_RAW n'est jamais utilisée comme source de fichiers M1.

**PROUVÉ** — Le builder :
- exige BASE_RAW taille `1490026496` et SHA-256 `efac0433da55eef42a0b990128744db6499e92f4292206ad56c3ec1e84d472f4` sur les 255 852 544 octets précédant `pmOS_root` ;
- copie `M0_TREE` dans son tree de travail ;
- prépare le chroot arm64 ;
- installe/configure M1 ;
- fabrique un nouvel ext4 `pmOS_root` de 4 Gio ;
- copie le BASE_RAW ;
- agrandit le raw à `4551868416` octets ;
- étend la GPT 4K ;
- remplace intégralement `pmOS_root` à partir du LBA `62464` ;
- produit l'Android sparse ;
- reconvertit sparse → raw et exige l'identité bit-à-bit.

## A3. Commande du build de référence

Le golden D-repro-01 est désormais l'enveloppe BASE_RAW candidate admise par le garde-fou local préparé. La chaîne complète reste à exécuter pour valider cette nouvelle voie de build.

Commande historiquement validée, transposée à l'entrée actuelle du dépôt :

```sh
clear
cd /home/linuxagent/ProjetMobian && INSTALL_OPTIONAL_APPS=1 ./build.sh /chemin/vers/Mobian-M0-userdata-rootfs-330-display-preflight.img /home/linuxagent/ProjetMobian-ancien-workspace/Mobian-M0/rootfs-m0-display-work archi-validation-02
```

**HISTORIQUE** — Le placeholder ci-dessus représente le préflight exact utilisé par `archi-validation-01`, aujourd'hui manquant. Pour la voie actuelle, le garde-fou local a été adapté afin d'admettre le golden D-repro-01 sur l'identité de son préfixe hérité. Cette nouvelle voie n'est pas encore validée par un build complet ni par le téléphone.

## A4. Applications optionnelles

`INSTALL_OPTIONAL_APPS=1` active `apps/scripts/install.sh`.

Liste acceptée au 15 septembre 2026 :

`epiphany-browser, gnome-console, gnome-calculator, gnome-text-editor, papers, showtime, gnome-clocks, gnome-weather, gnome-contacts, gnome-calls, chatty, megapixels, gnome-calendar, gnome-maps, geary, amberol, krecorder, koko`

Loupe et Lollypop sont retirés ; Showtime est l'unique lecteur vidéo ; Papers remplace Evince.

## A5. Profil debug préparé, NON VALIDÉ

`INSTALL_DEBUG_TOOLS=1` active `debug/scripts/install.sh`.

Profil préparé :

`gdb systemd-coredump strace ltrace gstreamer1.0-tools powertop linux-perf valgrind`

**PROUVÉ** — La modification est préparée dans l'arbre de travail.

**NON VALIDÉ** — Aucun build réel n'a encore validé cette option. Elle ne fait donc pas partie du dernier build de référence validé.

Pour le prochain build de validation, décider explicitement si `INSTALL_DEBUG_TOOLS=1` doit être activé. Ne pas attribuer à `archi-validation-01` des outils debug qui n'y étaient pas validés.

---

# B. RECONSTRUCTION M0 AVEC LES ARTEFACTS CONSERVÉS

Cette voie ne reconstruit pas les 330 paquets depuis Internet. Elle utilise le tree M0 DISPLAY survivant.

## B1. Géométrie prouvée

Secteur logique : `4096`.

| Élément | Valeur |
| --- | --- |
| taille raw M0 | `1490026496` |
| secteurs | `363776` |
| GUID disque | `20f69d00-01ef-4f28-98d5-152e69f32ddf` |
| `pmOS_boot` | LBA `2048–62463` |
| `pmOS_root` | LBA `62464–363519` |
| taille root | `301056 × 4096 = 1233125376` |
| offset root | `255852544` |
| UUID root | `dba94dfe-0fb9-4f95-970e-22949f4e69dc` |

`fdisk -l -b 4096` doit être utilisé pour lire correctement cette GPT. Une lecture implicite en secteurs 512 peut faire croire à tort que la table est absente.

## B2. Recette ext4 effectivement réexécutée le 15 septembre

Entrée :

`/home/linuxagent/ProjetMobian-ancien-workspace/Mobian-M0/rootfs-m0-display-work`

Sortie de test :

`/home/linuxagent/ProjetMobian-ancien-workspace/Mobian-M0/Mobian-M0-pmOS_root-rebuild-test.ext4`

Commande réexécutée :

```sh
clear
truncate -s 1233125376 /home/linuxagent/ProjetMobian-ancien-workspace/Mobian-M0/Mobian-M0-pmOS_root-rebuild-test.ext4 && mke2fs -t ext4 -F -b 4096 -I 256 -N 75360 -m 5 -L pmOS_root -U dba94dfe-0fb9-4f95-970e-22949f4e69dc -O '^metadata_csum,^metadata_csum_seed,has_journal,ext_attr,resize_inode,dir_index,orphan_file,filetype,extent,64bit,flex_bg,sparse_super,large_file,huge_file,dir_nlink,extra_isize' -E lazy_itable_init=0,lazy_journal_init=0 -d /home/linuxagent/ProjetMobian-ancien-workspace/Mobian-M0/rootfs-m0-display-work /home/linuxagent/ProjetMobian-ancien-workspace/Mobian-M0/Mobian-M0-pmOS_root-rebuild-test.ext4 301056
```

Résultat :
- taille : `1233125376`
- SHA-256 : `12384dd5c42b4fd28bdf4892694029fa8324b2331a5c725c39194931698fb490`
- `e2fsck -fn` : propre.

**PROUVÉ** — La version `mke2fs` actuelle est la même que celle du log historique : `1.47.2 (1-Jan-2025)`.

**PROUVÉ** — Ce nouvel ext4 n'est pas bit-identique à l'ext4 DISPLAY historique SHA `5377e414...`. Des métadonnées générées diffèrent au minimum : timestamps de création et `Directory Hash Seed`. Le simple écart de SHA ne prouve donc pas une divergence fonctionnelle du tree.

## B3. Assemblage raw réexécuté le 15 septembre

Sortie :

`/home/linuxagent/ProjetMobian-ancien-workspace/Mobian-M0/Mobian-M0-userdata-rebuild-test.img`

```sh
clear
cp --reflink=auto --sparse=always /home/linuxagent/D-repro-01-userdata-rootfs-ssh-key-weston-post-clear-v2.img /home/linuxagent/ProjetMobian-ancien-workspace/Mobian-M0/Mobian-M0-userdata-rebuild-test.img && dd if=/home/linuxagent/ProjetMobian-ancien-workspace/Mobian-M0/Mobian-M0-pmOS_root-rebuild-test.ext4 of=/home/linuxagent/ProjetMobian-ancien-workspace/Mobian-M0/Mobian-M0-userdata-rebuild-test.img bs=4096 seek=62464 count=301056 conv=notrunc,fsync status=progress
```

Résultat raw :
- taille : `1490026496`
- SHA-256 : `956bdf486262d578ffc6c196eb05bbdc730fe97c51656261610f042ccf850a5e`.

**PROUVÉ** — Les `255852544` octets précédant `pmOS_root` sont bit-à-bit identiques au golden.

**PROUVÉ** — La `pmOS_root` embarquée est bit-à-bit identique au nouvel ext4 injecté.

**PROUVÉ** — `fdisk -l -b 4096` retrouve les deux partitions aux bornes historiques.

## B4. Preuve historique du M0 DISPLAY bit-à-bit

Il faut distinguer le test local précédent de la preuve historique.

**PROUVÉ historiquement** :
- ext4 DISPLAY historique : SHA `5377e414237b6c3f4de4d3f8b6574f56605bcf1222382a059598d5ee6e0b4119`
- raw M0 DISPLAY historique : SHA `9f933e38966139bbb76bf96d2728e9620058dcb84028122d9b8974e333b966be`
- golden + remplacement intégral de `pmOS_root` par cet ext4 a reproduit le raw DISPLAY bit-à-bit.

Le fichier ext4 historique exact n'est pas actuellement disponible dans les emplacements locaux inspectés ; le tree survivant permet une nouvelle fabrication fonctionnellement cohérente, mais pas le même SHA ext4.

---

# C. TRANSITION `rootfs-final-330 → rootfs-m0-display-work`

L'ancien document disait que toute la transition était inconnue. C'était trop pessimiste.

## C1. Ce qui est maintenant retrouvé

**PROUVÉ** — Le journal Codex du 1er septembre conserve la chaîne :
- `rootfs-final-330`
- copie vers `rootfs-m0-dv43-work`
- ajout contrôlé du marqueur `usr/share/kernel/xiaomi-lmi/kernel.release`
- copie vers `rootfs-m0-display-work`
- modifications DISPLAY successives dans ce dernier tree.

**PROUVÉ** — La copie vers DISPLAY a été vérifiée à l'époque avec `15728` chemins des deux côtés et identité des types/UID/GID avant les modifications DISPLAY.

**PROUVÉ** — Les étapes DISPLAY sont documentées comme jalons successifs :
- script de libération du splash/KMS ;
- unité `lmi-splash-release.service` ;
- configuration seatd non-VT ;
- configuration Weston M0 ;
- création/activation de `weston-m0.service`.

Le journal conserve également la validation statique `systemd-analyze --root=... verify` et l'activation de `weston-m0.service`.

## C2. Ce qui manque encore

**INCONNU / INCOMPLET** — Nous n'avons pas encore, dans une source canonique unique, **la totalité des commandes exactes et contenus exacts** qui transforment un `rootfs-final-330` fraîchement reconstruit en tree DISPLAY.

Les sources intermédiaires `Mobian-M0/weston-m0/` survivent, mais leur simple présence ne prouve pas que chaque fichier correspond exactement au dernier état installé dans le tree. Les comparaisons déjà effectuées ont montré que certains basenames ne se retrouvent pas tels quels et que `weston-m0.service` / `weston.ini` diffèrent de copies intermédiaires conservées.

Conclusion : la transition n'est plus « inconnue » ; **sa structure et plusieurs opérations sont prouvées, mais sa recette exhaustive autonome reste incomplète**.

Cela ne bloque pas la voie B tant que `rootfs-m0-display-work` est conservé. Cela bloque une reconstruction réellement A → Z depuis les `.deb`.

---

# D. RECONSTRUCTION RÉELLEMENT DE ZÉRO DE `rootfs-final-330`

## D1. Recette connue

**PROUVÉ** — `base/scripts/build-unshare-330-inner.sh` :
- vérifie les SHA des archives ;
- peuple `local-repo-330` ;
- crée les métadonnées APT ;
- invoque `mmdebstrap --mode=unshare` avec les 330 `package=version` exacts ;
- produit un répertoire `rootfs-final-330`.

Le build historique s'est terminé avec :

`I: success in 281.2702 seconds`

## D2. Entrées manquantes

**PROUVÉ** — `m0-minimal-closure.tsv` conserve 330 entrées avec identité, version, architecture, taille et SHA-256.

**PROUVÉ** — `m0-minimal-debs.sha256` décrit 332 archives physiques ; deux sont des anciennes versions OpenSSL non retenues par la closure finale.

**PROUVÉ** — Le workspace survivant ne contient pas les 330 archives exactes. `local-repo-330` est vide et seule une petite fraction des `.deb` subsiste ailleurs.

**BLOQUEUR POUR LE « DE ZÉRO HISTORIQUE »** — Il faut récupérer **les objets `.deb` exacts** et vérifier chacun contre les SHA historiques. Le nom/version seuls ne suffisent pas à prouver l'identité binaire.

Les anciens chemins absolus de `m0-minimal-closure.tsv` pointent vers `/home/linuxagent/pmos-d-repro-01/...`, supprimé ; le consommateur doit donc être adapté ou le manifest réécrit sans changer les identités/SHA attendus.

## D3. Nouvelle acquisition préparée — ne pas confondre avec la closure historique

Des fichiers non encore validés ont été préparés :
- `base/files/m0-direct-packages.txt`
- `base/files/M0-ACQUISITION.md`
- `base/scripts/acquire-m0-closure.sh`
- `base/scripts/acquire-m0-closure.py`

Ils définissent 16 racines fonctionnelles et une nouvelle acquisition depuis dépôts publics.

**NON VALIDÉ / NOUVELLE RÉFÉRENCE** — Cette acquisition n'est pas une preuve qu'elle reproduira les 330 archives historiques. Elle peut produire une nouvelle closure avec versions/dépendances différentes. Elle ne doit pas être utilisée pour prétendre reconstruire bit-à-bit le M0 historique.

---

# E. LE PROBLÈME BASE_RAW M1

## E1. Ce que le builder consomme réellement

**PROUVÉ** — Le BASE_RAW n'est utilisé que pour :
- contrôle existence/taille/SHA ;
- copie vers le raw de sortie.

Après cette copie, le builder agrandit le disque, réécrit la GPT nécessaire et injecte un nouvel ext4 de 4 Gio à partir du LBA `62464`.

**PROUVÉ** — L'ancienne `pmOS_root` est intégralement écrasée. Aucun fichier de cette ancienne root n'alimente le M1.

**PROUVÉ** — `pmOS_boot` est conservée et devient celle du M1. Sa tranche validée a le SHA :
`6e2a1555a629126907c452a455ba12e78ee7e3862bbc39e376215569d9e7e03b`.

Filesystem :
- ext2
- label `pmOS_boot`
- UUID `7bd723c2-51d6-4015-b28b-2b38191bf765`
- blocs 4K.

## E2. Faut-il absolument reproduire `b12eeb3c...` ?

**NON.**

**PROUVÉ** — La reproduction bit-à-bit du préflight global `b12eeb3c...` n'est pas nécessaire au contenu M1 final : toute l'ancienne `pmOS_root` est écrasée.

**PROUVÉ** — Le golden D-repro-01 fournit l'enveloppe héritée nécessaire. Ses 255 852 544 premiers octets ont le SHA-256 `efac0433da55eef42a0b990128744db6499e92f4292206ad56c3ec1e84d472f4`. Après copie, agrandissement à 4 551 868 416 octets et application de `expand-gpt-4k.py` avec `root_start=62464` et `root_blocks=1048576`, ce préfixe est bit-à-bit identique à celui de `output/archi-validation-01.img`.

**NON VALIDÉ** — Le build M1 complet avec cette nouvelle admission et son essai sur téléphone restent à effectuer.

## E3. Adaptation d'admission préparée

Le contrôle SHA n'a pas été supprimé aveuglément. Le garde-fou global historique a été remplacé localement par :
- taille BASE_RAW exacte : `1490026496` ;
- SHA-256 exact des 255 852 544 octets réellement hérités avant `pmOS_root` : `efac0433da55eef42a0b990128744db6499e92f4292206ad56c3ec1e84d472f4`.

**PROUVÉ hors build** — Le golden D-repro-01 satisfait ce contrat et son enveloppe transformée reproduit exactement le préfixe du M1 validé.

**NON VALIDÉ** — Aucun build M1 complet ni test téléphone n'a encore été effectué avec ce nouveau garde-fou.

**À VALIDER EXPÉRIMENTALEMENT** — Aucun patch correspondant n'est encore déclaré validé.

---

# F. PRÉREQUIS HÔTE ÉTABLIS PAR LES SCRIPTS / LOGS

Ne pas transformer cette section en liste de paquets à installer : seules les capacités/outils effectivement observés sont listés.

## Pour M1 actuel

**PROUVÉ par le builder** :
- Bash ;
- `unshare` avec subordinate UID/GID mapping utilisé par le projet ;
- namespace de montage ;
- `binfmt_misc` ;
- `/usr/lib/binfmt.d/qemu-aarch64.conf` ;
- chroot arm64 via QEMU/binfmt ;
- `mount` avec bind/rbind et tmpfs ;
- `cp`, `dd`, `truncate`, `cmp`, `sha256sum` ;
- outils ext4 utilisés par le builder (`mke2fs`/`mkfs.ext4`, `e2fsck`) ;
- `img2simg` et `simg2img` ;
- Python 3 pour `expand-gpt-4k.py` ;
- accès APT aux dépôts Debian/Mobian pendant la préparation M1, puisque le builder exécute `apt-get update/install`.

## Pour reconstruction M0-330 historique

**PROUVÉ** :
- `mmdebstrap` ;
- `unshare` / user namespaces ;
- outils de dépôt/paquets appelés par le script ;
- les keyrings historiques ;
- les 330 `.deb` exacts.

## Pour GPU72

Le GPU72 possède en plus sa propre chaîne de compilation/source/sysroot documentée dans le dépôt. Ne pas déduire que cette compilation doit être refaite à chaque userdata si les artefacts GPU72 intégrés attendus sont déjà disponibles et que le builder les consomme.

---

# G. KERNEL / BOOT : CE QUI EST SÉPARÉ DU USERDATA

Le kernel n'est **pas** construit par `build.sh` userdata.

La chaîne kernel/device actuelle de référence est séparée :

`/home/mobian1/mobian-device`

branche historique de travail : `wip/xiaomi-lmi-6.8`

entrée : `build.sh`

sorties connues :
- `/home/mobian1/mobian-device/build/flash.sh`
- `mobian-device-xiaomi-lmi.tar.gz`

**PROUVÉ** — Le userdata contient un disque imbriqué GPT avec `pmOS_boot` et `pmOS_root`, mais le téléphone possède également sa partition Android `boot` contenant le boot image kernel/initramfs/DTB. Ne pas confondre ces deux niveaux.

**RÈGLE OPÉRATIONNELLE** — Si le prochain travail ne change que le userspace/rootfs M1 et que le boot/kernel actuellement validé reste compatible, **il n'est pas nécessaire de reconstruire le kernel**. Reconstruire le kernel seulement lorsqu'un changement kernel/DTB/initramfs/boot est réellement visé.

---

# H. VALIDATIONS DU RÉSULTAT

Le build n'est pas « validé » au seul fait que le script termine.

## H1. Validation hôte attendue

Le builder historique validé effectue/produit les contrôles suivants :
- ext4 final de `4294967296` octets ;
- label/UUID `pmOS_root` attendus ;
- `e2fsck` propre ;
- raw final de `4551868416` octets ;
- GPT 4K étendue ;
- Android sparse ;
- `simg2img` du sparse vers raw ;
- `cmp` bit-à-bit entre raw final et round-trip ;
- SHA-256 des artefacts.

Pour les images M0 4K, utiliser explicitement `fdisk -l -b 4096` pour la lecture de GPT.

## H2. Validation téléphone

Une validation hôte ne remplace pas le téléphone.

Le jalon matériel doit confirmer au minimum que le userdata :
- boote avec le boot/kernel de référence ;
- atteint le système attendu ;
- conserve le chemin USB/SSH nécessaire au diagnostic ;
- démarre Phosh ;
- permet l'interaction de base attendue.

Les fonctions additionnelles (GPU, Wi-Fi, Bluetooth, modem, etc.) ne doivent être déclarées validées que selon leurs documents de jalon respectifs.

---

# I. JOURNAL DES BUILDS / IDENTITÉS DE RÉFÉRENCE

## `archi-validation-01` — référence actuelle connue

Entrées historiques :
- BASE_RAW : préflight SHA `b12eeb3c561a37e84f2a99037587fdf833979a3b6f4610a03d4e820a51ae6399`
- M0_TREE : `rootfs-m0-display-work`
- `INSTALL_OPTIONAL_APPS=1`.

Sorties :

| Artefact | Taille | SHA-256 |
| --- | ---: | --- |
| ext4 M1 de travail | `4294967296` | `60de98660991379cb1d463ebadc7de43b73242d68f73502308e3891d2350844d` |
| raw userdata | `4551868416` | `559d6c44f2aa2223f91fd8af1db7a838b8183d7a223ceb80f7bdd13a9b6e31e4` |
| Android sparse | `2834813356` | `f61c19a09881c9a7ac165cc5e36ab08f146d65acddae2de18a6bb555c10663b3` |

**PROUVÉ** — ext4 et raw ont passé les validations hôte consignées ; le sparse round-trip est contrôlé.

**PROUVÉ par l'état projet consolidé** — la génération M1/Phosh, puis GPU72, a été validée sur téléphone dans les jalons correspondants. Ne pas attribuer à `archi-validation-01` une option debug préparée après coup.

---

# J. CE QUI EST ACTUEL, CE QUI EST HISTORIQUE

## Procédure actuelle recommandée

- dépôt `/home/linuxagent/ProjetMobian` ;
- `build.sh` ;
- `phosh/scripts/build-m1-phosh.sh` ;
- `apps/scripts/install.sh` via `INSTALL_OPTIONAL_APPS=1` ;
- `debug/scripts/install.sh` via `INSTALL_DEBUG_TOOLS=1`, **non encore validé** ;
- M0_TREE survivant comme entrée tant que la reconstruction de zéro n'est pas finalisée ;
- admission BASE_RAW par préfixe hérité préparée et validée hors build ;
- prochaine étape technique : refaire un build complet de validation avec le golden D-repro-01, puis valider le résultat sur téléphone.

## Reconstruction historique utile

- golden D-repro-01 ;
- closure M0-330 et manifests ;
- `rootfs-m0-display-work` ;
- recette ext4/GPT M0 ;
- validations M0 BASE/DISPLAY ;
- ancien préflight comme identité de référence.

## À ne plus utiliser comme méthode actuelle

- anciennes variantes D114/D115/R145 pour fabriquer M0 : géométrie différente ;
- anciens chemins `/home/linuxagent/pmos-d-repro-01` : supprimés ;
- anciens builds M1 comme entrée du nouveau M1 : le builder actuel reconstruit depuis M0 ;
- anciennes expériences pmbootstrap v18–v27 comme procédure Mobian M1 actuelle ;
- hypothèse qu'un simple SHA différent de l'ext4 reconstruit signifie un rootfs fonctionnellement différent ;
- lecture GPT M0 en secteurs 512.

---

# K. BLOQUEURS RÉELS AU 15 SEPTEMBRE 2026

Pour refaire **un M1 fonctionnel à partir des artefacts survivants** :
1. exécuter le build complet avec le garde-fou BASE_RAW par préfixe hérité et le golden D-repro-01 ;
2. valider hôte ;
3. valider téléphone.

Pour refaire **bit-à-bit le préflight historique** :
- la transformation exacte vers `b12eeb3c...` reste inconnue.

Pour refaire **M0 depuis zéro sans `rootfs-m0-display-work`** :
- récupérer les 330 `.deb` exacts ;
- adapter les chemins de la closure sans changer ses identités ;
- reconstruire `rootfs-final-330` ;
- compléter/canoniser la transition `rootfs-final-330 → rootfs-m0-display-work` ;
- comparer le tree obtenu à la référence survivante.

Pour intégrer **le profil debug** :
- faire un build avec `INSTALL_DEBUG_TOOLS=1` ;
- vérifier les paquets et le comportement hôte ;
- valider sur téléphone.

---

# L. PROCHAIN JALON DOCUMENTAIRE APRÈS LE FUTUR BUILD

Après un build réussi par la nouvelle voie, mettre à jour ce document avec :
- identité exacte du BASE_RAW admis ;
- patch/contrat d'admission retenu ;
- commande exacte réellement exécutée ;
- versions/outils hôte observés ;
- SHA et tailles ext4/raw/sparse ;
- résultat `simg2img` + `cmp` ;
- résultat téléphone ;
- statut du profil debug ;
- commit Git correspondant.

À ce moment seulement, la réponse à « peut-on refaire le build validé sans les conversations ? » pourra devenir **OUI**.

---

# ANNEXE — RAPPORT D'ENQUÊTE CONSERVÉ

La suite conserve les preuves et la chronologie du document précédent. En cas de contradiction, la partie A–L ci-dessus représente l'état consolidé le plus récent ; les anciennes formulations restent présentes comme historique de l'enquête et doivent être lues avec leur date/statut.


# Golden M0, géométrie et préflight historique M1

État consolidé de l'enquête sur la reproductibilité M0 → M1 (14 septembre 2026). Ce document réunit les preuves et les lacunes ; **ce n'est pas une procédure de build de zéro validée**. `/home/linuxagent/pmos-d-repro-01` est un chemin historique supprimé. Le workspace survivant est notamment `/home/linuxagent/ProjetMobian-ancien-workspace/Mobian-M0`. Ci-dessous, `logs/`, `manifests/` et `measure-closure.sh` désignent ce répertoire M0 ; `pmbootstrap-work/` se trouve à la racine de `ProjetMobian-ancien-workspace`. Le golden D-repro-01, les images M0 et le préflight M1 sont trois objets distincts.

## Deux entrées M1 distinctes

**PROUVÉ** — `build.sh` transmet séparément `BASE_RAW` (image disque M0) et `M0_TREE` (arborescence installée) à `phosh/scripts/build-m1-phosh.sh`. Celui-ci contrôle taille et SHA du premier, copie le second et y prépare le système M1. Il n'extrait pas `M0_TREE` du BASE_RAW. Preuves : `build.sh:8-16,42-47` ; `phosh/scripts/build-m1-phosh.sh:22-27,43-48,91,387-396`.

**PROUVÉ** — Le build `archi-validation-01` a reçu le préflight M0 comme BASE_RAW et `rootfs-m0-display-work` comme M0_TREE (`/home/linuxagent/.bash_history:1684` ; `docs/status/ACTIVE-GPU72.md:99-105`). Son raw M1 validé survit dans `output/archi-validation-01.img` (`docs/CURRENT-BUILD.md:28-66`).

## Rootfs M0 et closure exacte

**PROUVÉ** — Le bootstrap initial utilise `debootstrap --foreign --arch=arm64 --variant=minbase trixie`, puis la seconde étape sous `proot`/QEMU (`8d3e32d:mobian/bootstrap-final.sh:4-22`). `logs/apt-minimal-install.log:4-5,118-120,372,386` montre `ca-certificates 20250419` et `mobian-archive-keyring 20251117.0` déjà installés, 249 nouveaux paquets, 148 MB à télécharger, 574 MB installés annoncés, le téléchargement achevé et un échec ultérieur à la configuration de `systemd` sous `proot`.

**TRÈS PROBABLE** — Cet échec a laissé les `.deb` dans le cache APT. `measure-closure.sh:4-31` mesure cet ancien cache, ajoute l'archive du keyring Mobian et déduplique les versions par nom de paquet. **INCONNU** — La commande exacte ayant produit `apt-minimal-install.log` et la liste des paquets demandés explicitement à APT ; « 249 nouveaux paquets » n'établit pas cette liste.

**PROUVÉ** — Les données suivantes survivent dans `ProjetMobian-ancien-workspace/Mobian-M0/manifests/` :

- `m0-minimal-closure.tsv` : **330 paquets**, avec nom, version, architecture, Installed-Size, taille du `.deb`, SHA-256 et ancien chemin absolu. `m0-minimal-totals.txt` indique **181 127 132 octets** de téléchargements et **721 909 760 octets** d'Installed-Size. Ces totaux ne concernent pas seulement les 249 nouvelles installations du journal APT.
- `m0-minimal-debs.sha256` : **332 archives physiques**. Les deux archives supplémentaires sont les anciennes versions `libssl3t64 3.5.6-1~deb13u2` et `openssl-provider-legacy 3.5.6-1~deb13u2` ; la closure conserve `3.5.7-1~deb13u2` pour chacune.

**PROUVÉ** — La recette versionnée de `rootfs-final-330` vérifie le SHA des `.deb`, peuple `local-repo-330`, crée les métadonnées APT et invoque `mmdebstrap --mode=unshare` avec les 330 `package=version` (`8d3e32d:mobian/build-unshare-330-inner.sh:4-71` ; `base/scripts/build-unshare-330-inner.sh:5-70`). Elle produit un **répertoire**, pas une image. `logs/mmdebstrap-unshare-330.log` termine par `I: success in 281.2702 seconds`.

**PROUVÉ** — Le workspace conservé ne contient plus l'ensemble des 330 `.deb` exacts : `local-repo-330` est vide ; 15 `.deb` seulement se trouvent ailleurs sous `Mobian-M0`. `rootfs-final-330` n'y subsiste plus. Manifests, keyrings, outils, logs et `rootfs-m0-display-work` subsistent. Les chemins du manifest pointent toujours vers `/home/linuxagent/pmos-d-repro-01/Mobian-M0/rootfs/var/cache/apt/archives`, disparu, tandis que le script exige ces fichiers et leurs SHA (`base/scripts/build-unshare-330-inner.sh:23-27`). Les noms, versions, tailles et SHA permettent d'identifier les archives exactes, **sans garantir leur disponibilité actuelle**. Ce manque concerne la recréation de `rootfs-final-330` depuis les paquets, pas l'assemblage de l'image M0 DISPLAY sauvegardée.

**TRÈS PROBABLE** — `rootfs-m0-display-work` est un dérivé installé de la génération M0-330 avec adaptations DISPLAY ; c'est le M0_TREE réellement utilisé par M1. **INCONNU** — La séquence exhaustive et reproductible `rootfs-final-330` → `rootfs-m0-display-work` et la liste complète des changements. Les deux répertoires ne doivent pas être déclarés identiques. Cette transition n'est pas nécessaire pour réassembler le raw M0 DISPLAY depuis le golden et l'ext4 DISPLAY déjà sauvegardés.

## Origine du golden récupéré et sort du préflight historique

**PROUVÉ** — `pmbootstrap-work/log.txt:1127-1128,1182-1188` consigne `truncate -s 1421M` pour créer `xiaomi-lmi.img`, puis `parted` pour sa GPT. `8d3e32d:historical/scripts/21_build_pmos_v27_full_reproducible.sh:34-50,146` décrit `pmbootstrap install --zap --no-fde --sector-size 4096 --no-sparse` et la copie de l'image produite. C'est une méthode **postmarketOS v27**, pas une preuve de création du préflight Mobian M0.

**PROUVÉ** — Le golden historique `D-repro-01-userdata-rootfs-ssh-key-weston-post-clear-v2.android-sparse.img` a été récupéré depuis le backup. Après conversion sparse → raw, `D-repro-01-userdata-rootfs-ssh-key-weston-post-clear-v2.img` mesure **1 490 026 496 octets** et son SHA-256 est **`4ec785b85d48494847b81e6a02a74486725affe7707bd3de2dd466d91206be11`**. Le raw récupéré est disponible localement ; il fournit les octets exacts hors `pmOS_root`, y compris GPT et `pmOS_boot`. Ce golden n'est ni le M0 DISPLAY ni le préflight M1.

**PROUVÉ** — Le BASE_RAW exact attendu par le builder M1 était **un autre fichier**, `Mobian-M0-userdata-rootfs-330-display-preflight.img`, taille **1 490 026 496 octets**, SHA-256 **`b12eeb3c561a37e84f2a99037587fdf833979a3b6f4610a03d4e820a51ae6399`** (`phosh/scripts/build-m1-phosh.sh:22-23,47-48`). `/home/linuxagent/.bash_history:1684` atteste son usage et la ligne **1872** consigne `rm -f` de son emplacement déplacé sous `ProjetMobian-ancien-workspace/output/`. La recherche antérieure d'une copie de taille et SHA attendus sous `/home/linuxagent` a été négative. Sa suppression à cet emplacement est documentée ; **sa reproduction bit pour bit n'est pas établie**. Le golden récupéré n'a pas le SHA exigé par M1.

**INCONNU** — La transformation exacte ayant produit le préflight SHA `b12eeb3c...` depuis le M0 DISPLAY ou son rootfs, ainsi que sa commande historique. Le remplacement intégral de `pmOS_root` est maintenant **PROUVÉ pour le M0 DISPLAY**, mais cette preuve ne reconstitue pas le préflight M1 et ne démontre pas qu'il est identique au M0 DISPLAY.

## Géométrie et octets utiles au builder M1

**PROUVÉ** — La géométrie M0 est consignée dans `ProjetMobian-ancien-workspace/home-archives/redmi-k30-pro-postmarketos-reproduction/notes/d-repro-01-2026-08-29.md:145-162` et les scripts `historical/weston/{control,post-clear}/build_userdata.py`. La GPT du M1 survivant a été inspectée avec ses CRC.

| Élément | Golden et raw M0 DISPLAY | Raw M1 `archi-validation-01.img` |
| --- | ---: | ---: |
| Taille | 1 490 026 496 octets | 4 551 868 416 octets |
| Secteurs de 4 096 octets | 363 776 | 1 111 296 |
| GUID disque | `20f69d00-01ef-4f28-98d5-152e69f32ddf` | conservé |
| `pmOS_boot` | LBA 2048–62463, 60 416 secteurs, ext2 | mêmes bornes et mêmes octets |
| `pmOS_root` | LBA 62464–363519, 301 056 secteurs | LBA 62464–1111039, 1 048 576 secteurs |
| Après root | 251 secteurs libres + 4 de table GPT + 1 d'en-tête | même organisation à la nouvelle fin |

**PROUVÉ** — `pmOS_root` commence à l'offset **255 852 544** (LBA **62 464** à secteurs de **4 096 octets**). Sa taille historique est **1 233 125 376 octets**, soit **301 056 blocs** de 4 096 octets ; son dernier octet est **1 488 977 919**. Les SHA-256 des raw sauvegardés sont **`df323c63878533be9b8e44f2d3999466496c8d60c51e9b1961b8a5c4f7119965`** pour le M0 normal et **`9f933e38966139bbb76bf96d2728e9620058dcb84028122d9b8974e333b966be`** pour le M0 DISPLAY. Pour chacun, **tous les octets avant et après `pmOS_root` sont identiques au golden** : les différences sont confinées à la partition root. Leur assemblage consiste donc à conserver le golden hors root et à y placer le contenu root propre à chaque variante ; l'essai de reconstruction bit pour bit ci-dessous porte spécifiquement sur DISPLAY.

**PROUVÉ historiquement / référence d'archive** — `Mobian-M0-DISPLAY-pmOS_root.ext4` est documenté comme mesurant **1 233 125 376 octets**, SHA-256 **`5377e414237b6c3f4de4d3f8b6574f56605bcf1222382a059598d5ee6e0b4119`**. Une reconstruction historique documentée a copié le raw golden puis remplacé **l'intégralité** de `pmOS_root` par cet ext4, avec l'équivalent de :

```sh
dd if=Mobian-M0-DISPLAY-pmOS_root.ext4 of=Mobian-M0-DISPLAY-reconstruction-test.img bs=4096 seek=62464 count=301056 conv=notrunc,fsync
```

Le raw reconstruit a obtenu le SHA-256 **`9f933e38966139bbb76bf96d2728e9620058dcb84028122d9b8974e333b966be`**, exactement celui du raw M0 DISPLAY récupéré dans le backup. Cette identité bit-à-bit est une **preuve historique consignée dans les archives**, et ne correspond pas au test local du 15 septembre, qui a produit un nouvel ext4 au SHA `12384dd5...`. La recette **golden D-repro-01 + remplacement intégral de `pmOS_root` = M0 DISPLAY** est donc prouvée ; la structure analogue du M0 normal est établie par l'identité des octets extérieurs à root, sans confondre son root avec l'ext4 DISPLAY.

**PROUVÉ** — La GPT M1 conserve le GUID de partition boot `64337b4d-7bea-4971-b03e-9083882c054c` (type EFI `c12a7328-f81f-11d2-ba4b-00a0c93ec93b`) et le GUID root `ef24217a-cf15-4f61-9633-cd279569a647` (type Linux root ARM64 `b921b045-1df0-41c3-af44-4c6f280d3fae`). Les deux entrées portent le nom GPT `primary` et les attributs `0`. `expand-gpt-4k.py` ne modifie pas ces champs.

**PROUVÉ** — `pmOS_boot` occupe les octets **8 388 608–255 852 543** (247 463 936 octets). La tranche du raw M1 et `output/archi-validation-01-partition1.bin` ont le même SHA-256 : **`6e2a1555a629126907c452a455ba12e78ee7e3862bbc39e376215569d9e7e03b`**. Le filesystem est ext2, label `pmOS_boot`, UUID `7bd723c2-51d6-4015-b28b-2b38191bf765`, blocs 4K. Le builder ne réécrit pas cette partition : ses octets M1 viennent du BASE_RAW accepté.

**PROUVÉ** — Le builder crée un nouvel ext4 de **4 294 967 296 octets** depuis M0_TREE, copie le BASE_RAW, agrandit la copie, modifie la GPT et écrit **tout** le nouvel ext4 à partir de l'octet **255 852 544** jusqu'à **4 550 819 839** (`phosh/scripts/build-m1-phosh.sh:387-396`). L'ancienne root (octets 255 852 544–1 488 977 919), l'ancien espace après root et l'ancienne GPT secondaire sont entièrement recouverts. Aucun octet de l'ancienne root n'alimente le résultat M1. Le garde-fou local actuel ne couvre donc plus ces octets destinés à être écrasés.

**PROUVÉ** — `phosh/scripts/expand-gpt-4k.py:11-50` conserve l'espace LBA 6–2047, réécrit quatre octets du protective MBR, les 92 premiers octets de l'en-tête GPT primaire et sa table, puis crée une GPT secondaire à la nouvelle fin. Le raw M1 conserve GUID, types, attributs et noms de partitions. La taille M0 et l'ancienne borne root sont désormais vérifiables sur le golden récupéré, qui conserve aussi **les octets exacts de l'ancienne GPT secondaire**. Celle-ci est recouverte par le nouvel ext4 dans le M1 et ne sert pas à son résultat.

**PROUVÉ pour l'enveloppe héritée** — Le golden D-repro-01 peut servir de BASE_RAW au sens des octets conservés par M1. Après les transformations normales de `expand-gpt-4k.py`, ses 255 852 544 premiers octets sont bit-à-bit identiques à ceux de `archi-validation-01`. **NON VALIDÉ** — Le résultat pratique de la chaîne complète : aucun build M1 complet avec cette admission ni essai téléphone correspondant n'est encore établi.

**PROUVÉ** — L'ancien contrôle par SHA global portait aussi sur les octets ensuite écrasés. L'admission locale actuelle contrôle à la place la taille exacte et le SHA de **tout le préfixe réellement hérité**, ce qui couvre en une seule identité le MBR, la GPT primaire, les espaces conservés et toute `pmOS_boot`. Le garde-fou passe avec le golden réel et le script reste syntaxiquement valide. **NON VALIDÉ** — Le comportement de la chaîne complète reste à confirmer par un build puis par le téléphone.

## Chronologie Git synthétique

**PROUVÉ** — L'enquête a parcouru les **56 commits accessibles**, du premier `8d3e32d` (31 août) à HEAD `d2911e1` (14 septembre), leurs arbres, références et reflogs. Histoire linéaire, une seule branche locale et ses références `origin`, aucun tag ni stash. Le reflog conserve `3256f1b`, première incarnation du commit initial avec **le même arbre** que `8d3e32d`. Huit blobs isolés contiennent notes, README ou AGENTS, sans recette M0 supplémentaire. Aucun `.img`, `.ext4`, `.tar` ou raw de la chaîne n'a été suivi ; `.gitignore:1-52` exclut ces artefacts.

| Commit(s), date | Génération, changement et statut |
| --- | --- |
| `8d3e32d`, 31 août | Import pmbootstrap v27, variantes userdata **D-repro-01** modifiées par `debugfs`, bootstrap/closure/mmdebstrap M0-330. **Historique** ; les variantes D-repro-01 ne sont pas le préflight M0. |
| `56ae176`, 1er septembre ; `15f5d24`, 2 septembre | Configuration M0 BASE/DISPLAY et validation Weston. Des ext4/raw/sparse construits sont mentionnés, sans commande d'assemblage suivie dans Git. **Validé historiquement** ; l'assemblage golden + ext4 DISPLAY est désormais **PROUVÉ expérimentalement**, sans établir la commande historique exacte. |
| `c538d66`, 3 septembre ; commits M1 des 3–12 septembre | Le builder M1 apparaît en **consommant déjà** le préflight M0 et `rootfs-m0-display-work` ; les générations suivantes changent le système M1, pas la fabrication du parent. **Historique puis validé**. |
| `5e6dbb0`, `98d88a9`, 12 septembre | Variantes de `build-unshare-330-inner.sh` pour rootfs GPU71 puis `rootfs-final-gpu72` ; **répertoires**, pas raw. **Historique**. |
| `be25432`, 13 septembre ; `d2911e1`, 14 septembre | Documentation M0 puis déplacement vers `base/`, `phosh/` et `historical/`. Aucun script supprimé ou renommé retrouvé ne fabrique le préflight. **Actuel**. |

**PROUVÉ** — `Mobian-M0-pmOS_root.ext4`, `Mobian-M0-DISPLAY-pmOS_root.ext4`, `mobian-m0-root-display.ext4` et `mobian-m0-rootfs-display.tar` n'apparaissent ni comme chemins suivis ni dans les versions textuelles inspectées de Git ; leurs traces relèvent du workspace non versionné. Manifests M0, `.deb`, caches, images et arbres générés n'ont pas non plus été suivis. **INCONNU** — L'existence d'un script local perdu hors Git : son absence de Git ne prouve pas son inexistence passée.


## Mise à jour du 15 septembre 2026 — recette M0 DISPLAY effectivement reconstruite

Cette section distingue explicitement la **recette historique prouvée** de la **reconstruction effectuée le 15 septembre 2026** dans le workspace survivant.

### État des artefacts disponibles aujourd'hui

**PROUVÉ** — Le golden suivant est présent localement :

`/home/linuxagent/D-repro-01-userdata-rootfs-ssh-key-weston-post-clear-v2.img`

SHA-256 :

`4ec785b85d48494847b81e6a02a74486725affe7707bd3de2dd466d91206be11`

Taille : **1 490 026 496 octets**.

Ce golden constitue l'**enveloppe** du M0 : GPT, `pmOS_boot` et tous les octets hors `pmOS_root` sont conservés tels quels lors de la reconstruction.

**PROUVÉ** — Le tree M0 DISPLAY conservé est :

`/home/linuxagent/ProjetMobian-ancien-workspace/Mobian-M0/rootfs-m0-display-work`

Sa taille est d'environ **731 MiB**.

**PROUVÉ** — Le **package-set installé du tree correspond exactement aux 330 triplets paquet/version/architecture** du manifeste :

`manifests/m0-minimal-closure.tsv`

La comparaison des trois premières colonnes triées est vide. Les validations historiques `dpkg-audit.txt`, `non-installed-states.tsv` et `package-set.diff` sont également vides.

**PROUVÉ** — Les éléments critiques suivants correspondent exactement aux copies de validation conservées :

- `10-usb0.network` : SHA `af6ec67a...`
- configuration SSH key-only : SHA `47399978...`
- `authorized_keys` : SHA `4c0543a8...`
- `usr/share/kernel/xiaomi-lmi/kernel.release` : SHA `57e55963...`

### Recette M0 DISPLAY reconstruite

La recette effectivement utilisée est :

1. **Copier le golden** sans le modifier.
2. Construire un nouvel ext4 `pmOS_root` de :
   - **301056 blocs**
   - blocs de **4096 octets**
   - **75360 inodes**
   - UUID `dba94dfe-0fb9-4f95-970e-22949f4e69dc`
   - label `pmOS_root`
   - journal de **8192 blocs**
3. Peupler cet ext4 directement depuis :
   `rootfs-m0-display-work`
   avec `mke2fs -d`.
4. Vérifier le nouvel ext4 avec `e2fsck -fn`.
5. Remplacer dans une copie du golden la zone `pmOS_root` :
   - LBA de départ : **62464**
   - offset : **255852544 octets**
   - longueur : **301056 × 4096 = 1233125376 octets**
6. Vérifier que les octets avant `pmOS_root` sont inchangés.
7. Vérifier que l'ext4 injecté est exactement celui qui a été construit.
8. Vérifier la GPT avec `fdisk -l -b 4096`.

Le userdata de contrôle effectivement produit le 15 septembre est :

`/home/linuxagent/ProjetMobian-ancien-workspace/Mobian-M0/Mobian-M0-userdata-rebuild-test.img`

SHA-256 :

`956bdf486262d578ffc6c196eb05bbdc730fe97c51656261610f042ccf850a5e`

Le `pmOS_root` reconstruit a le SHA :

`12384dd5c42b4fd28bdf4892694029fa8324b2331a5c725c39194931698fb490`

et sa taille est exactement `1233125376` octets.

**PROUVÉ** — `e2fsck -fn` termine avec les cinq passes sans erreur.

**PROUVÉ** — Les octets précédant `pmOS_root` sont identiques au golden.

**PROUVÉ** — La zone `pmOS_root` du userdata reconstruit est identique bit pour bit au nouvel ext4 injecté.

**PROUVÉ** — La GPT lue avec des secteurs de 4096 octets donne exactement :

| Partition | Début | Fin | Secteurs |
| --- | ---: | ---: | ---: |
| p1 | 2048 | 62463 | 60416 |
| p2 | 62464 | 363519 | 301056 |

### Pourquoi le nouveau SHA du rootfs n'est pas celui de l'ancien

**PROUVÉ** — La reconstruction du `pmOS_root` depuis le tree donne `12384dd5...`, et non le SHA historique `5377e414...`.

Cela **ne constitue pas une preuve de différence fonctionnelle du contenu du tree**. `dumpe2fs` montre notamment des métadonnées générées lors de la nouvelle création du filesystem, dont :

- date de création du filesystem ;
- date du dernier contrôle ;
- `Directory Hash Seed`.

La reconstruction n'est donc **pas bit-identique à l'ancien ext4 historique** avec les éléments actuellement disponibles.

**IMPORTANT** — Le SHA historique `5377e414...` et le raw M0 DISPLAY `9f933e38...` restent des références historiques consignées dans les archives. Aucun ancien ext4 de 1–2 Gio n'a été retrouvé dans les emplacements locaux inspectés le 15 septembre. Le disque de sauvegarde `D:` contenant potentiellement les artefacts de travail n'est pas disponible depuis ce poste.

### Conclusion opérationnelle

La recette suivante est désormais considérée comme **reproductible fonctionnellement avec les artefacts actuellement conservés** :

`golden M0`
→ copie
→ `mkfs.ext4` 4K de 301056 blocs depuis `rootfs-m0-display-work`
→ injection à LBA 62464
→ vérification ext4
→ vérification GPT 4K.

Elle **ne doit pas être décrite comme une reproduction bit-à-bit du M0 DISPLAY historique** tant que l'ancien `pmOS_root.ext4` n'a pas été récupéré ou que le raw historique n'a pas été comparé au résultat.

Cette recette est distincte de la reproduction du **préflight M1** `b12eeb3c...`, dont la transformation historique exacte reste inconnue.

## PIÈCES ENCORE MANQUANTES POUR UN BUILD DE ZÉRO

**PROUVÉ historiquement** — Le golden D-repro-01 combiné à l'ext4 root DISPLAY historique de SHA-256 `5377e414237b6c3f4de4d3f8b6574f56605bcf1222382a059598d5ee6e0b4119` reconstruit **bit pour bit le M0 DISPLAY** de SHA-256 `9f933e38966139bbb76bf96d2728e9620058dcb84028122d9b8974e333b966be`. **Cet ext4 historique exact n'est actuellement pas disponible localement.** Avec les artefacts physiquement disponibles, `rootfs-m0-display-work` permet de reconstruire un nouvel ext4 (`12384dd5...`) puis un raw (`956bdf48...`) de géométrie et de contenu fonctionnellement cohérents, mais **non bit-identiques aux références historiques**. La conception hypothétique d'un nouveau BASE_RAW à GPT arbitraire n'est donc pas requise pour cette reconstruction actuelle, mais la reproduction bit-à-bit du M0 DISPLAY exige toujours de retrouver l'ext4 historique exact (ou un artefact équivalent permettant de le restituer). Le M0 normal sauvegardé partage lui aussi tous ses octets hors root avec le golden. Ces acquis ne sont pas une recréation du préflight M1.

Pour **refaire un M1 fonctionnel** à partir du M0 DISPLAY connu, les points restants sont distincts :

1. **PROUVÉ, admission préparée** — Le builder local contrôle désormais l'identité des 255 852 544 octets réellement hérités plutôt que le SHA global du préflight historique. Le golden D-repro-01 satisfait ce contrôle et son préfixe transformé reproduit bit-à-bit celui du M1 validé.
2. **INCONNU, validation restante** — Construire et contrôler un M1 complet par cette voie, puis valider le userdata produit sur téléphone. Le M1 historique `archi-validation-01` a été validé, mais pas cette nouvelle entrée.

Pour **reproduire bit pour bit le préflight historique** `Mobian-M0-userdata-rootfs-330-display-preflight.img` de SHA `b12eeb3c...` :

3. **INCONNU, travail restant** — Identifier et prouver la transformation exacte depuis le M0 DISPLAY ou son rootfs, puis comparer le résultat au SHA attendu. Aucun préflight historique identique n'a été recréé.

Pour **reconstruire réellement depuis zéro `rootfs-final-330` et sa descendance DISPLAY** :

4. **PROUVÉ, travail restant** — Récupérer/reconstruire les **330 `.deb` exacts** de la closure et vérifier taille, version, architecture et SHA. Les manifests les identifient mais ne garantissent pas leur disponibilité ; aucun téléchargement n'a été tenté.
5. **PROUVÉ, travail restant** — Corriger les anciens chemins absolus de `m0-minimal-closure.tsv` ou adapter son consommateur. Les SHA attendus doivent rester ceux des archives exactes.
6. **INCONNU, travail restant** — Reconstituer et vérifier la transition reproductible `rootfs-final-330` → `rootfs-m0-display-work`, y compris les adaptations DISPLAY. L'existence du second ne fournit pas la recette exhaustive.

Les points 4–6 ne sont **pas nécessaires** pour reconstruire l'image M0 DISPLAY déjà sauvegardée à partir du golden et de son ext4. La possibilité d'un M1 fonctionnel via une entrée adaptée, la reproduction bit pour bit du préflight historique et la reconstruction du rootfs depuis les 330 paquets exacts demeurent trois objectifs distincts.
linuxagent@AsusTUFGaming:~$