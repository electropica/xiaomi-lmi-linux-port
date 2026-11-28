# ADSP stop incident — 27 November 2026

A supervised `remoteproc` stop caused LPASS clock warnings, then a synchronous external abort in `qcom_swrm_cpu_reg_read` during SoundWire runtime resume and WCD938x IRQ cleanup. The stack passed through GLINK/APR removal during `rproc_stop_subdevices`; code review places that before the remoteproc driver's actual power-off operation. The exact missing dependency or ordering failure has not been established. No power saving can be inferred from this failed test.

The scheduled recovery reboot became stuck during shutdown and required a manual long press. After restart, ADSP reported `running`, the RTC loader was active and charging was detected. A scheduled reboot is therefore not a guarantee of unattended recovery after a kernel fault. Do not repeat the ADSP stop on the strength of this record.
