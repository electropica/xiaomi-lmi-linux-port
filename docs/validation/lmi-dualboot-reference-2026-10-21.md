# Passive reference before dual-boot installation — October 21, 2026

This observation used the existing Mobian installation, RPMh kernel and
qualified homedrag7/Phoc/GSD/NPU policies. The separate dual-boot artifacts were
built on the host during the observation; none was installed on the handset.
No phone contact occurred between the operator's unplug and explicit replug.

The USB-poll-bounded interval lasted 32761.930
seconds (9.101 hours). Displayed capacity was 100% at departure
and 79% at the last USB-off sample, 724.845 seconds
before detected replug. The 79% charging-return reading is not a separate pure
discharge endpoint. Temperature at departure/last USB-off sample was
21.7/17.7 C; learned capacity remained 2677 mAh. Wi-Fi stayed enabled.

Clock-accounted suspension totalled 31221.930 seconds, or
95.299% of the interval, including the normal initial
fifteen-minute awake delay. All 38 exact msoc-delta resumes
were observed with the screen logically locked and no unblank through the next
suspend callback. They returned toward suspension after
15.183–15.423 seconds.
Logical lock/ScreenSaver state is not an electrical panel-power measurement.

Thirty-nine qualified USB-off suspend brackets cover
30523.038 seconds. Estimated rates are:

| Gauge channel | Estimated mA |
|---|---:|
| Software charge counter | 52.209 |
| Shadow counter | 51.577 |
| Nominal-scaled raw counter | 87.291 |

The channels share the fuel gauge and different capacity scales; these are not
three independent physical current measurements. Thirty-four filtered-current
readings at resume endpoints more than an hour after unplug had a median of
49.324 mA, range
49.265–50.514 mA.
Endpoint readings do not integrate current throughout suspension. The residual
order remains similar to earlier observations; no new cause or battery-saving
effect is established by this unchanged-policy reference.

Retrieval confirmed the same boot, observer inactive with Result=success,
charging resumed, empty RTC alarm and no pending NPU recovery state. Phosh and
GSD remained active with zero recorded restarts. No new observation or policy
change was armed on return. Private event-log SHA-256:
`087a9445066ccdf850967989318ac05a7bba737babf7fe4d7afc3286174e77a5`. Raw telemetry remains private.
