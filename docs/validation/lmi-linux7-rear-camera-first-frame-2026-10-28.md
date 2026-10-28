# Linux 7 : première trame de la caméra arrière — 28 octobre 2026

Sur le Poco F2 Pro, avec le noyau communautaire caméra et torche, la caméra arrière OV13B10 est détectée. Les formats du chemin média ont été vérifiés en mode TRY, puis une seule trame a été acquise par `/dev/video0` avec des liens temporaires et les formats et liens initiaux restaurés et relus.

- Chemin observé : OV13B10 → CSIPHY1 → CSID0 → VFE0 RDI0 → vidéo0.
- Format accepté et capturé : SGRBG10P, 1364 × 768, un plan, 1712 octets par ligne, 1 314 816 octets. Une image de scène est visible après forte amplification ; la trame est très sombre et bruitée.
- Le producteur PipeWire existant exige une capture monoplane NV12 et ne peut donc pas exploiter ce flux multiplan Bayer. L'aperçu dans Snapshot, la qualité, l'exposition et les performances restent à développer et qualifier.
- Le décodeur de diagnostic doit respecter la disposition RAW10 décrite par la documentation V4L2 (quatre octets de poids forts suivis d'un octet contenant les deux bits faibles de chaque pixel), l'ordre GRBG et le remplissage des lignes.
- Il ne s'agit pas d'une validation de l'appareil photo complet ni de la caméra avant. Aucune modification du noyau ou installation supplémentaire n'a été effectuée pour cette capture.

Le premier outil de diagnostic proposé présentait des divergences d'ABI et une énumération pouvant boucler ; une lecture a précédé un écran noir et un redémarrage forcé. Le lien causal avec le blocage ou la veille reste inconnu. Une copie corrigée a été contrôlée par tailles, offsets et numéros ioctl, dont compilation ARM64 et exécution sous émulation ; ses réglages ont été restaurés après l'acquisition. Les journaux et l'image restent privés.

