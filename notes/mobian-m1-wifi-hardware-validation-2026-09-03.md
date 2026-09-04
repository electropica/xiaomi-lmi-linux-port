# Mobian M1 lmi Wi-Fi hardware validation — 2026-09-03

**MANUAL HARDWARE VALIDATION PASSED**  
**SYSTEMD LOW-LEVEL AUTOMATION HARDWARE-VALIDATED ON 2026-09-04**

The test used the POCO F2 Pro / Redmi K30 Pro (`lmi`), the D-v43 downstream
4.19.325 kernel, and the Mobian M1 userspace. All stock Android partitions
were mounted read-only. No firmware, Android binary, APEX, persist content, or
Wi-Fi credential is stored in this repository.

The successful order was: mount modem/system/vendor/runtime APEX/persist;
prepare `/data/vendor/wifi`; expose the stock QCA6390 firmware and vendor WLAN
configuration; start `qrtr-ns`; start the stock `/vendor/bin/cnss-daemon` with
the project property shim and verify its forked child; write `fs_ready` once;
wait eight seconds; write `ON` once; then wait for the WLAN interface.

CNSS connected to WLFW over QRTR, loaded `regdb_j11.bin`, dynamically selected
and loaded `bd_j11gl.elf`, sent M3, received `FW_READY`, and completed the host
driver probe using `WCNSS_qcom_cfg.ini` and `wlan_mac.bin`. The kernel created
`wlp1s0`, `p2p0`, and `wifi-aware0`. NetworkManager found 7–8 BSS entries,
associated with a WPA2 network, obtained `192.168.4.121/24` by DHCP, and
installed a default route through `192.168.4.1`. The independent `usb0` SSH
path remained operational.

Do not force `bd_j11.elf`: the exact kernel selected `bd_j11gl.elf`
successfully. Modern Debian `rmtfs`, `tqftpserv`, and `pd-mapper` are not part
of this proven path. A failed activation must not automatically repeat
`fs_ready` or `ON` within the same boot.

## Automated M1 REPRO v2 result

The tracked systemd sequence subsequently passed on hardware through all
low-level stages: read-only mounts, firmware preparation, qrtr-ns,
cnss-daemon, the single `fs_ready` write and delay, the single `ON` write,
`FW_READY`, qcacld probe, and creation of `wlp1s0`, P2P, and Wi-Fi Aware
interfaces. All three per-boot attempt markers were present.

The tested image did not contain `wpasupplicant`, so NetworkManager initially
reported the Wi-Fi device as unavailable and could not D-Bus activate a
supplicant. Installing `wpasupplicant 2:2.10-24` and its normal Debian
dependencies at runtime changed the device to disconnected, enabled scanning,
and allowed WPA2 association, DHCP, DNS, a default route, and successful APT
access. This runtime result justifies adding the package to the next recipe;
it does not embed the tested network profile or credential.

## Integrated M1 REPRO v3 result

M1 REPRO v3 validated the complete automated path with Debian
`wpasupplicant 2:2.10-24` already installed and enabled. The low-level systemd
sequence completed once, `wlan0` appeared, NetworkManager listed SSIDs, and a
CLI WPA2 connection obtained DHCP, DNS, a default route, and Internet access.
USB networking and SSH remained available. No tested Wi-Fi profile or secret
is stored in the image recipe or repository.

The original v3 image did not validate Phosh's Wi-Fi controls: it lacked a
normal interactive logind session, and its NetworkManager actions were blocked
by Polkit. A later clean runtime experiment added only `PAMName=login` and
`XDG_SEAT=seat0`, created an active graphical logind session without a VT, and
validated ordinary NetworkManager authorization and UI radio/profile control.
`settings.modify.system` remains an administrative action. No broad permissive
rule is part of the implementation. See
`notes/mobian-m1-phosh-logind-polkit-validation-2026-09-04.md`.
