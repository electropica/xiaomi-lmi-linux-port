# Mobian M1 lmi Wi-Fi hardware validation — 2026-09-03

**MANUAL HARDWARE VALIDATION PASSED**  
**SYSTEMD AUTOMATION NOT YET HARDWARE-VALIDATED**

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
