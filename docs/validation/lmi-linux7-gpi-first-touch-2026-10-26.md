# Linux7 lmi GPI allocation and first touch events — 26 October 2026

## Hardware result and limits

The operator temporarily booted menu 841183652938bd3bc8ebdbbd59e48dc6ff6509439448f58ce30cda729452dc46. This was RAM boot, not a flash. The observed kernel was 6642f7fc4f8e6dd3f09e70da5e12c48c419d7fcc7176ea25fa9e013a486d248a, DTB 6a7c630401e0805e976bac3d01d899112e369d16af9d0dc1b4d736f302ca1910, and observer initramfs feaac77aec44734d5ba4bd7ebb659f83f2bbc7fab6191472164a0554adb0eb19.

The preceding touch2 trial failed at GPI event-channel allocation (EV ALLOCATE completion timeout), before the I2C adapter and touchscreen could register. The candidate changes only the GPI base offset for the experimental xiaomi,lmi-sm8250-gpi-dma compatible, plus that compatible in this board's GPI1 node. Other mainline SM8250 matches retain their prior behavior.

In the new trial:
- GPI1 provider binds successfully.
- I2C a94000 probe returns zero after approximately 32.5 ms.
- EDT device 13-0038 registers an input device and binds successfully.
- The preceding GPI allocation timeout is absent.
- A bounded operator-triggered capture returns 591 input_event records, 275 MT-coordinate updates and 113 synchronization reports.
- Captured MT coordinates lie within the declared 1080x2400 geometry: X130..889, Y405..2131.

This is hardware evidence that the candidate crosses the prior DMA allocation boundary and produces touch events. It is not a qualification of complete touchscreen behavior, display, a desktop, suspend or battery operation.

## Remaining release defect

Four tracking IDs started, but only one tracking ID ended; BTN_TOUCH was asserted and did not return to zero in the capture. The operator confirms multiple fingers were used and all were removed before capture ended. Therefore this trial does not qualify multi-touch release.

The retained Xiaomi driver explicitly reconciles the previously active contact mask against the current report, releasing contacts absent from it. The upstream EDT driver path used in this trial reports explicit UP records but does not perform that reconciliation. A board-only candidate uses input_mt_drop_unused() at the end of each successfully read snapshot and reads the ten-contact report configured for this handset (63 bytes, within the existing read buffer). It preserves the successful GPI and power-order candidates and leaves generic boards unchanged.

That release candidate has passed source/syntax and private-overlay checks only. No Image has been built and no hardware release trial has occurred.

## Evidence retention

Raw journals and touch records are local/private; do not commit them, because bootloader command lines contain identifiers. Local evidence directory:
work/linux7-touch-20261026T220939350276Z-private/
Capture SHA256: 795fefa4979fcfac90e7a2fe3b4add1c381f784dbadc94e14e402ffcb4ffc8b8.
RESULT.json, EVENT_REVIEW.json and VALIDATION.json distinguish DMA success from incomplete release behavior.

The existing Mobian 4.19 and permanent menu have not been changed by this trial.


## Bounded release trial result (26 October 2026)

The operator booted the release candidate kernel a44101ed50e7eefea6c793cc477fefa492a01666774161f76d4c1077c8d1afc7.
The captured interval contains 40 tracking-ID starts and 40 releases, empty final
active slots and BTN_TOUCH=0, with no SYN_DROPPED. I2C/EDT bind and the previous
GPI timeout is absent. This passes the release check in the captured interval.
The raw byte cap was reached after 12.901885 seconds of events, before the
30-second hands-off reminder; do not claim a complete minute or quiet final
phase. GUI, display and ten-finger qualification remain pending.
Evidence remains local/private under work/linux7-touch-20261026T223017387301Z-private.
The next investigation is a direct RAM test of the pinned ccc007ccc7.1 tree,
with its author-specific initramfs/cmdline settings adapted to this menu.
