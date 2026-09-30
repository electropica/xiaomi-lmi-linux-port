# TFA9874 OEM-container provenance for Xiaomi lmi

## Revision provenance

The retained 2026-09-29 research note referenced the LineageOS branches
`lineage-23.2` and `lineage-20`, but did not record their commit IDs. The exact
historical revisions originally consulted therefore cannot be recovered from
the retained evidence. The following official manifests were independently
resolved and inspected on 2026-09-30. These dated checks provide immutable
references; they are not asserted to be the revisions consulted during the
earlier research:

- Xiaomi lmi, commit
  [`1f0372de77c5068880273bd2f8e3552fa55be3a0`](https://github.com/LineageOS/android_device_xiaomi_lmi/blob/1f0372de77c5068880273bd2f8e3552fa55be3a0/proprietary-files.txt)
  (`lineage-23.2` at verification time).
- Xiaomi Platina, commit
  [`d29905355c49d1529e5ab55162274efa224f475c`](https://github.com/LineageOS/android_device_xiaomi_platina/blob/d29905355c49d1529e5ab55162274efa224f475c/proprietary-files.txt)
  (`lineage-20` at verification time).

## Findings and limits

The lmi proprietary-file manifest at the pinned revision lists the generic
`vendor/firmware/tfa98xx.cnt` container. This establishes that the extraction
manifest includes a generic-named TFA container; it does not establish that
its tuning is acoustically appropriate for every lmi speaker, nor does it
authenticate a particular device's runtime firmware contents.

The Platina manifest lists `tfa98xx_aac.cnt` and `tfa98xx_goer.cnt`. Those
names document variants for another device only. They are not authenticated
lmi candidates, and their presence there is not evidence that either variant
matches lmi hardware.

The available lmi-focused evidence did not authenticate an AAC- or GOER-named
container for lmi. This is not proof that no such variant exists in every
historical release, region, vendor image, or unexamined source. The generic
container's presence and successful loading are likewise not proof of
speaker-specific acoustic tuning. The low observed output level therefore
remains unresolved; no candidate firmware is recommended by this provenance
record.

No proprietary firmware, private device identifiers, local paths, or private
logs are included here. For the current audio milestone and its remaining
limits, see [the dated audio progress record](../validation/archi-validation-02-audio-progress-2026-09-29.md).
