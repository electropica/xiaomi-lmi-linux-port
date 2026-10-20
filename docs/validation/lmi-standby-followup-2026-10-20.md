# Standby and fuel-gauge follow-up — 20 October 2026

This is a retained observation and bounded source review, not a battery fix.
No kernel, charger policy, calibration, learned capacity or protection changed.

## Corrected overnight observation

The collector without the explicit charge_done getter ran for 7 h 17 min unplugged.
Linux callback-clock accounting records 6 h 54 min suspended (about 95%, including
normal initial idle delay).27 sleep/resume pairs were preserved:25 msoc-delta,
1 msoc-high and1 USB return. Reported capacity changed 92% to 79%. On return the
collector was inactive/successful, RTC wake alarm empty and charging resumed.

In 25 USB0 brackets individually >99% suspended, modeled averages are 43.615 mA
software, 43.451 mA shadow and 86.007 mA raw.23 USB0 resume samples strictly more
than 1 hour after unplug give filtered-current median 49.313 mA (49.261–53.684).
These are related gauge outputs, not independent calibrated current channels.
The median describes sampled wake moments, not a time-weighted overnight mean.
Counter increases, missing status/scales and charge-contaminated USB return
endpoints are excluded from counter aggregates. No causal comparison with the
previous charge_done-reading observer is asserted.

Independent offline replay reproduced the retained accounting. Coarse starting
SOC bands confirm the already observed association:90–92% brackets yield
52.79 mA software versus 85.97 mA raw;80–89% yield 41.87 versus 86.01 mA. Time order,
SOC and temperature covary; this is not a controlled physical-load comparison.

## SRAM access chain and review correction

The reviewer initially reported fg_sram_read unavailable. It is present in the
supplied fg-util.c at line 628. fg_get_sram_prop calls it with FG_IMA_DEFAULT;
fg_sram_read votes SRAM_READ awake, locks access, selects DMA/interleaved mode,
unlocks and releases its vote after the transfer, including a transfer error.
PM8150B selection in qpnp-fg-gen4.c explicitly sets use_dma=true.

fg_direct_mem_read reaches __fg_direct_mem_rw and its request/release helpers
in fg-memif.c. Completed transfers and checked request failures attempt memory
access release. fg_direct_mem_release clears access before arbitration: if
its first register write fails it returns before the second clear. This is a
conditional cleanup limitation, not an observed handset fault or a justified
kernel change. The retained current-boot journal search inspected 53,493 lines
and found no matching request/grant/release/SRAM error messages; log absence
is not proof of fault absence.

The IBAT_FLT path reads SRAM, decodes packed signed 24-bit data using 19073/10000
microamps per code, and propagates ordinary access failures. No reviewed normal
path clips or substitutes 49 mA. Host code does not establish firmware filter
update cadence while suspended. Memory reads themselves briefly interact with
the arbiter and awake voting; they must not be described as zero-overhead.

## Cached recharge threshold qualification

A source-verified cached battery/recharge_vbat read returned -22. In the retained
smb5-lib.c, smblib_dynamic_recharge_vbat returns immediately while
chg->auto_recharge_vbat<0. The 4380 mV fallback in that function therefore is not
an active threshold at this snapshot. This neither disables all hardware
recharge behavior nor explains the residual unplugged estimates. No explicit
charge_done read or recharge setting write was performed.

## Next evidence boundary

A physical current measurement would separate gauge-model outputs, but an
in-series battery monitor requires additional hardware and opening the phone;
it is not scheduled. Existing full-Android records lack matched raw/shadow/
filtered series. A further comparison must add those missing channels or a
specific causal discriminator, rather than repeat an identical standby run or
assume recovery is equivalent to full Android. No new build is justified yet.
