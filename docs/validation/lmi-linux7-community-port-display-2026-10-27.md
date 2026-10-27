# Linux 7.2.12 community boot/display port: first hardware milestone

The operator saw a white screen followed by console text. The strict observer
receiver confirms `7.2.12-lmi-community-port1` and the expected kernel, DTB and
initramfs hashes. The RAM menu was
`99dcf5f303c6d412a3bb2e5cacc55a165a1262d605e5fc59fb34918177d7df9e`.

The retained 129,425-byte capture has SHA256
`ba5f473d989d602234e77201b24c26cc9425e1a92cd05242657e98ebfec2d604`.
DSI binds at 3.067957 s; DRM MSM initializes at 3.212974 s; the MSM framebuffer
appears at 3.428206 s. USB and UFS probes complete successfully. Observer
heartbeats cover uptime 4.34 through 94.38 s. No kernel-panic, BUG or RCU-stall
marker is present in this capture. This is bounded evidence, not a long-term
stability test. Actual panel takeover is established, beyond bootloader video.

The source port therefore preserves the community 7.1 display/USB milestone
on Linux 7.2.12. Touch remains deliberately disabled. GPU acceleration is not
qualified: a650 firmware is absent from this small diagnostic initramfs, as
are ADSP, Bluetooth and WLAN firmware. Audio has pending probe dependencies.
No root filesystem or Mobian GUI is mounted; no battery/suspend result follows.

The permanent Mobian/Lineage installation was not flashed. Windows required
manual Remote NDIS driver association before USB journal collection; future
observer USB-descriptor work should address that separate host-side friction.
Next development milestone: port the already qualified lmi touch supplies and
release handling onto this display-capable 7.2.12 base, then validate them.
