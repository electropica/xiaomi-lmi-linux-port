# Linux 7 Type-C detach detection — 1 November 2026

With kernel `e826b049...`, an awake unplug test observed input VBUS at zero,
the Type-C attach and VBUS-detect bits clear, and CC/VBUS/attach IRQ counters
advance, while the TCPM power supply stayed online and UPower still reported
`OnBattery=false` for seven readings. This is an observed wrong power-source
state; it is not a physical current measurement.

The preserved source and object from the matching build used a hard IRQ
handler returning `IRQ_HANDLED` even though a threaded handler was registered.
In this kernel's IRQ core, `IRQ_WAKE_THREAD` is needed to run that thread,
which forwards VBUS and CC changes to TCPM. The candidate changed that return
only. Its compiler output returned 2 (`IRQ_WAKE_THREAD`) rather than 1.

The operator installed the resulting permanent menu. The first 72,349,696 bytes
of the boot partition were read back and matched the built image SHA-256
`656220aa26406c9d7fba20eda121869c86126b98077b0283ca52b593bc4e1212`.
The running kernel reported candidate identity `f87c1afc...`. After an
operator-assisted disconnect, seven consecutive samples recorded VBUS zero,
TCPM online zero and UPower `OnBattery=true`. After reconnection UPower
reported `OnBattery=false`. This establishes correct detection for this
awake unplug/replug trial, not every Type-C/PD or suspend scenario. The battery
status after reconnect was discharging at that instant and does not establish
charging performance.

The previous AC-idle workaround was reversed on the handset: AC idle action is
again `nothing`; battery idle action remains `suspend` with a 900-second
timeout. The `lmi-current` schema defaults were restored to match. The
previous workaround was observed to allow one unattended s2idle interval; a
new idle test under correct battery detection remains to be performed.

The first boot reached the desktop, then the graphical session stopped and
the operator saw a stationary console; a forced reboot restored the desktop.
The retained journal shows a `phosh-m0.service` stop but does not establish
its initiator or a kernel panic; pstore was empty. This event remains under
investigation and is not attributed to the Type-C change without evidence.

The wakeup patch and the one-line threaded-IRQ correction are retained as
experimental candidate patches. They are not integrated into a fresh complete
kernel/image recipe. Their presence alone must not be taken as a reproducible
release or as qualification of audio, charging, suspend wake and USB roles.
