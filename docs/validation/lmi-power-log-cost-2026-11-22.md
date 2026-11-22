# Awake logger A/B comparison

On 22 November 2026 the handset was physically unplugged, kept awake and screen-off, with Wi-Fi up. Phase A ran from 10:24:48 to 10:44:51 local time with `lmi-power-log.service` active; phase B ran until 11:04:52 with it stopped. The existing battery logger and an independent five-second observer remained active for both phases. The independent observer recorded battery current, status, coherent MSOC and mirror, backlight, temperature and radio state.

After removing the first three minutes of each 20-minute phase, 203 samples remained per phase. Mean signed battery currents were -127.951 mA (A) and -127.347 mA (B); both medians were -125.976 mA. The apparent difference in discharge magnitude is approximately 0.60 mA. The measurements are sequential, battery level and temperature shifted slightly, currents include sensor noise and the observer's own cost, and short bursts may fall between samples. One pair is not sufficient to resolve or exclude a small logger cost.

All 478 recorded phase samples reported `Discharging`, coherent MSOC and screen-off as required by the observer. Phase boundary states confirmed the logger active at the end of A and inactive at the end of B. A restoration timer was armed before stopping the service; the logger was restored at 11:04:52. The service was active, and the test and safety timer inactive, after reconnection. The exact effect in suspend was not measured: the logger process is frozen while the system is suspended.

The saved local event log SHA-256 is `cdb409724ed7860f338f333b38cac07944067d4a81d54ff7f0c7927f4a7ba10f`. It is not published because device logs may contain private information.
