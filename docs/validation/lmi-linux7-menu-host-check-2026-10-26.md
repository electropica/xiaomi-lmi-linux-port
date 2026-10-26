# Linux 7 observer menu: host checks and first default-OS trial

The operator temporarily booted menu SHA256
`128fcc748af5ee1d65825709e2ce287c7f25b8f5bb85209f4a8adcebbee6fc75`
and confirmed the default Mobian startup. Read-only runtime checks confirmed
the existing 4.19.325-cip128-st12 kernel and normal phosh-m0 session.
At that first checkpoint, Linux 7 had not run on the handset. No permanent
menu was installed. See the subsequent kernel-entry evidence below.

The first menu reused the older Mobian reference DTB, so its driver reported
Unknown Battery / design capacity zero. Do not use that trial for autonomy
comparisons. Revision rails1 restores the previously qualified passive profile
container ordering; all DT properties and other node ordering remain unchanged.

Independent review of the 7.2.12 minimal DTB found a missing RPMh regulator
parent compatible/PMIC ID and an incorrectly named LDO12 child. Revision rails1
adds the binding identifiers and correct child name. USB PHY voltage requests
match the downstream handset tree: L5 880mV, L12 1800mV, L2 3072mV.
Thirteen redundant inherited reservation copies are removed. Static coverage
checks find all 22 vendor ranges and no overlapping candidate reservations
(23 regions including the experimental ramoops area). This does not prove
firmware data retention, physical supply behavior or USB runtime operation.

Corrected Linux 7 DTB SHA256:
`cc29aabb5648f26901c76358f8c82f321eaf80753463cdeac75e4d7ef4079693`.
Corrected combined bundle SHA256:
`161a0fed8f4e547f761891ccade790fb67efc82de46ea5fcfcc4e31ce4f6bda1`.
The kernel Image is unchanged (7.2.12, not 7.3). The 64MiB outer and 32MiB FD
limits remain unchanged. Fifteen actual C parser/CRC tests, actual gzip and
extent-helper execution for both kernels, and five ARM64 syntax units pass.
These are host checks, not complete firmware or handset acceptance.

An isolated operator recipe is ready under ignored
`output/minimax-kernel7-feasibility/codex-linux7-menu/recipe-rails1/`.
It reuses the compiler rootfs and twenty pinned private source checkouts,
preserves the first built image, and writes only `firmware-output-rails1/`.
Codex has not launched this firmware build. Existing installed OSes and the
qualified rescue image remain unchanged. After the user build, inspect its
actual image/bundle hashes before another temporary boot; qualify default
Mobian/profile first, then the experimental observer with a prepared log reader.
No battery gain or complete hardware support is claimed.

## First Linux 7 kernel-entry evidence (subsequent trial)

The operator selected Linux7 from rails1 image5d2a9796..., observed a white
screen and automatic reset, then returned to installed Mobian. A read-only
capture from systemd's pstore archive preserved console-ramoops-0 (33063 bytes,
SHA2564f494cbc8f2af24a349c2a505dd0f8dcac1ea91cd9a0f79bde358846bde4f821).
It explicitly identifies Linux7.2.12 and the exact kernel, DTB and observer
hashes from rails1. All eight CPUs were activated; RPMh regulator requests were
initialized. The last preserved line is at0.128163s: memory-tier demotion targets.
No panic, initramfs-ready marker or USB journal was observed. Kernel entry is
proven; a complete boot, USB transport and hardware support are not.
The archived pmsg file contains older Android records and is not attributed to
this observer. Log preservation worked across this particular reset only;
future retention remains unguaranteed. Private raw logs remain outside Git.

Actual System.map places memory_tier_late_init before many later initcalls.
The unused-clock and unused-domain cutoff routines occur still later and log
entry messages absent from the capture. Their responsibility is unproved.
The next diagnostic changes only the previously empty Android header cmdline
to initcall_debug. Kernel, DTB, observer and complete firmware payload are byte
identical. Candidate image SHA256:
1d833660902eff17a552929e1a1990118439c55a58f625c4875f1e11dbf34c9c.
Whether ABL propagates this header argument still needs runtime confirmation.
No kernel or firmware rebuild, flash, idle-policy or clock-policy change was
performed. The launcher remains operator-run RAM boot with bounded USB reader.

## Probe diagnostic result: TLMM binding path and missing reserved GPIO ranges

The operator diagnostic Image c1bda374... and temporary menu e0549f68... reset
again. Read-only pstore capture preserved131060bytes, SHA256
9aa9000f8e2973cb16775045875ec4908a352c0593f6a9554ffadc946481871b.
It contains192 lmi7probe markers. smem completed and returned0. The next intact
pair names f100000.pinctrl / sm8250-pinctrl before runtime PM and supplier
checking, with no completion. At21.184047s RCU reported a stalled CPU0. This
localizes the binding path, not an exact instruction or electrically bad pin.

The pinned community lmi DTS (SHA256ca2dfa5282d023fb8d59895bc9fb192f0e4e4fc140c88d55b31bd08a2b911e01,
line1286) explicitly reserves GPIO28-31 and40-43. The deployed minimal DTB
omitted this property. The exact gpiolib.c source initializes the valid mask
before iterating direction reads, and excludes reserved lines before calling
msm_gpio_get_direction, which reads the TLMM control register. These source
facts support a specific candidate; they do not prove which read stalled.

Candidate tlmm1 adds only gpio-reserved-ranges=<28 4>,<40 4> to the TLMM node.
All other DT properties and node order compare identical; register bases are
not guessed or moved. DTB SHA256
9eff6beac1e5178c74a0db064520cec2d4e9c5a755eed50a8db9e610cd920170.
Bundle SHA256dcd67d9c7647a0526f78ea45e21cbff83890e7604e42134244f0fb36474bd277,
43106388bytes; only linux7/dtb differs from probe1. The diagnostic kernel,
observer, logging argument and all Mobian components remain byte-identical.
Host packing/property invariance and five ARM64 syntax units pass. The manual
menu build is prepared at output/minimax-kernel7-feasibility/codex-linux7-menu/recipe-tlmm1/.
No kernel rebuild, new phone trial, flash or power-policy change was performed.

## RAM observer and live USB accepted after GPIO reservation fix

The operator selected tlmm1 menu b953bb45... . The white screen persisted but
no automatic reset occurred. Windows detected the observer's USB gadget.
Its new RNDIS identity initially lacked a driver (code28). The operator bound
Microsoft's built-in Remote NDIS driver, then added the host USB address
172.16.42.2/24 through the scoped administrator script (ActiveStore, no gateway
or Wi-Fi changes). Windows driver binding is a host prerequisite, not a kernel
fix. Automatic descriptor matching remains a future observer improvement.

A single read-only USB TCP9000 capture yielded129909bytes, SHA256
44f056f599e9af52c5b0e482f4353e73974167b016f64395cfd9f07e146895ae.
It verifies7.2.12-dirty, diagnostic Imagec1bda374..., DTB9eff6bea... and the
unchanged observer7b070dd0... . The sm8250-pinctrl probe returns0 at0.186517s,
/init starts at0.266368s, USB binds at0.351140s and the observer is ready at
0.371535s. Heartbeats reach330.48s; the previous RCU stall marker is absent.
Raw capture/identifiers remain private outside Git.

With the same diagnostic kernel and observer, the reserved-range DT property
is the only board component changed since the failing probe1 trial. It
successfully crosses that observed TLMM binding blockage in this trial; the
precise offending GPIO/register remains unobserved. Do not claim full phone
support or an autonomy improvement. There is no graphical UI, rootfs mount,
Wi-Fi, touch, camera or battery qualification. CPUfreq remains deferred with
Failed to find icc paths, and some clock/interconnect sync_state dependencies
remain pending. The next project stage is real board/peripheral bring-up,
not another blind repetition of the same first-boot experiment. No permanent
menu was installed; the normal Mobian/Lineage reference remains unchanged.
