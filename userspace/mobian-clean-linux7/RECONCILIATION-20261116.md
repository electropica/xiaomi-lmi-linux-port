# Image recipe reconciliation — 16 November 2026

Comparison of archived project notes, the clean-image recipe, and read-only inspection of the running handset. This is not a complete image qualification or a claim that every historical change was ported.

| Area | Evidence and recipe decision | Remaining validation |
| --- | --- | --- |
| Boot and kernel | The running 7.2.12 menu image was matched to its archived image; the full boot partition was separately saved and hashed. The rootfs recipe does not replace the kernel. | Recovery has not been exercised. The candidate lot9g kernel lacks the current TFA98xx audio driver; it is not a replacement. |
| Phosh drawer | The handset runs the `+pulldownbubble1` versions of phosh, phosh-common and libphosh. The recipe requires all three matching packages and holds them; Julien reported no current drawer issue on 23 November. | Exact package files and checksums must be staged by the operator. Full image build and boot not retested. |
| Suspend and unwanted screen wakes | `CHASSIS=handset`, battery timeout configuration and the GSD `+sleeprefusal1` packages are included. USB PC guard in the recipe hashes identically to the handset. | No proof that every wake source is fixed; guard intentionally blocks suspend while the PC connection is active. |
| Audio | The ALSA routing, PipeWire speaker config and ADSP helper have the same hashes as the handset. A bounded VA codec probe retry is enabled in the recipe and on the handset; the user confirmed sound after manual reprobe. | Retry recovery at a fresh boot has not been tested. Audio kernel driver and firmware are separate external inputs. |
| Rear camera | Snapshot launcher and DMA heap udev rule match the handset; the required camera packages are included. The user confirmed a live preview. | Front pop-up camera remains research only; no candidate DTB or driver is included. |
| Keyboard | French input-source default, manual hide button and layer-shell dependency are included. The hide service is installed on the handset. | Existing per-user GSettings override image defaults; physical interaction with the restored button still needs confirmation. |
| Battery | Logger 0.1.1, viewer 0.1.10 and pre/post suspend boundary package are staged as separate local build inputs; a real s2idle pair was recorded. | No samples are claimed during suspend; the post sample in the supervised test was already charging. A complete new image build remains untested. |
| Music | Lollypop and its playlist import default are included. Existing sample playlists were restored on the handset, and the user confirmed the six-track playlist works. | Personal music, playlists, databases and other user files are not packaged in the rootfs; back up and restore them separately. Opening individual files need not append to the queue. |
| First-boot services | SSH, calls, camera permissions, zram and duplicate-GDM masks are checked. The recipe now sets Europe/Paris, matching the handset. | Calls and connection recovery are not requalified by this audit. |
| Wi-Fi and location | Wi-Fi reprobe and GeoClue helper are present and enabled. No profile credentials are included. | GPS functionality and Wi-Fi behaviour through sleep are not established by service status. |
| Orientation | No accelerometer is exposed in the current IIO inventory. | Automatic rotation is not a verified feature; do not claim it works. |

For a new build, stage the eight exact custom Debian packages and the three battery packages with their respective SHA256SUMS. The staged firmware and GPU stack remain local inputs. The recipe verification and syntax checks do not replace a full ARM64 image build, boot test, or preservation of the user's data.

## Rootfs build on 16 November

The operator built the staged rootfs after updating the unavailable linux-perf pin to `6.12.117-1`. Debos reported `LMI_IMAGE_VERIFIED`, `LMI_IMAGE_CLEANED` and `Recipe done`; a subsequent `xz -t` passed. The resulting `rootfs-arm64-phosh-linux7.tar.xz` has SHA-256 `614d507d2cf4f960bccb711d24443b075ce61bfa44204f4e507cb778da7dbd99`. This is a compressed root filesystem, not a bootable partition image; it has not been installed or boot-tested. Package staging, credentials, userdata, firmware and the built archive are local/private inputs or outputs.

On 17 November the viewer was updated to 0.1.12 after an overnight sleep began before the six-hour display window and was consequently hidden. The new version presents the full sleep boundary summary near the top and labels an overlap with the selected period; it does not invent samples during sleep. The November 16 archive predates this change and still contains 0.1.10; a future build requires the 0.1.12 package.

## GPU and firmware spot check

The preserved private overlay under `work/storage-resize-20261114/clean-recipe-candidate/overlays/` was compared to the handset on 16 November. All 37 firmware files and all 9 GPU files present in that overlay matched the SHA-256 of the corresponding handset paths. This checks file contents, not whether the overlay includes every file required by the system, symbolic-link topology, permissions or compatibility with another kernel. The private files are not published in Git.

The boot log reported missing `qca/htbtfw20.tlv`; BlueZ had no default controller. On 16 November two archived linux-firmware candidates (`htbtfw20.tlv`, `htnv20.bin`, provenance in `work/linux7-radio-firmware-20261027/PROVENANCE.json`) were installed on the handset and the QCA UART driver reprobed. The kernel then reported downloading both and completing UART setup, but BlueZ still had no controller and `hciconfig hci0 up` returned `Operation not supported`; hci0 remained `DOWN RAW`. The firmware files remain installed, but this is not a working Bluetooth fix and they are not yet a qualified image input. A separate modem firmware request for `qcom/sdx55m/sbl1.mbn` remains unresolved. Other early firmware failures for ADSP, WLAN and GPU must be interpreted in boot order: those files are present on the mounted root filesystem and later activity was observed.

Management configuration queried after the firmware test identifies the controller as unconfigured with `public-address` missing. The generic firmware's displayed address is not evidence of the handset's factory identity. No public address was written, no pairing was attempted, and the factory address source and persistence of a future correction remain to be determined.

The factory `bluetooth` partition was inspected by a temporary read-only mount. Its QCA firmware and NVM files differ from the archived generic versions. A reversible test using the two factory files completed UART setup but still reported `public-address` missing; the generic files were restored and the partition unmounted. This does not prove where the unique factory address is stored.

The earlier `docs/validation/mobian-m1-qca6390-hastings-hci-design-2026-09-05.md` describes the stock Android provisioning path: Xiaomi `nv_mac` obtains six bytes through vendor QMI NV operation `0x01bf`, writes `/data/vendor/mac_addr/bt.mac`, and an Android script supplies the Bluetooth property. This is static source analysis, not a successful read of the current device's NV address. The historical generic NVM placeholder matches the currently displayed placeholder and is not proof of a unique factory address. No QMI operation or address change has been performed in this investigation.

A bounded QRTR service lookup with temporary Debian tools on 16 November did find ADSP and WLAN services but did not list Xiaomi service `0xffe4`. This is a snapshot, not proof the service can never appear. The tools were extracted temporarily and not installed; no NV request or address write was made.
