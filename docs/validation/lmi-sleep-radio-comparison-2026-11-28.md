# Overnight radio comparison — 27–28 November 2026

Five approximately one-hour phases were run locally on battery, using two RTC wakes per phase. Each planned radio state was checked at the boundaries; the Wi-Fi driver and Bluetooth soft-block were restored afterwards. RTC wake and a completed suspend were observed for each half-hour. Regulator traces reported no buffer overruns. IRQ deltas include awake transitions and must not be presented as events exclusively during sleep.

| Phase | Displayed capacity | Raw MSOC | Approx. points/h | Estimated mA |
| --- | --- | --- | ---: | ---: |
| Baseline A | 85 → 80% | 217 → 206 | 4.30 | 113 |
| Bluetooth blocked | 80 → 77% | 206 → 196 | 3.91 | 102 |
| Wi-Fi PCI driver unbound | 77 → 73% | 196 → 186 | 3.91 | 102 |
| Both | 73 → 63% | 186 → 162 | 9.38 | 246 |
| Baseline B | 63 → 59% | 162 → 152 | 3.91 | 102 |

The mA figures use a previously learned 2,617 mAh capacity and the MSOC delta; they are estimates, not current measured throughout suspension. The combined phase lost 12 MSOC counts in each half-hour and its reported battery temperature rose from 18 to 21 °C. Those halves are not independent repeats. Gauge behavior, temperature and order effects have not been eliminated. The result merits a targeted baseline/combined/baseline repeat; it does not establish causation.

Wi-Fi interrupts decreased while its driver was absent. No additional global disable event was observed for the physical regulator providers shared with QCA; this does not expose individual consumer votes and does not measure rail current. The phone displayed 40% at 06:00. A later safety-monitor suspend request failed around 06:45 while another suspend was being initiated. The script did not preserve the failure's stderr, so the precise cause is unproven; low-battery monitoring was not guaranteed thereafter. At reconnection the phone reported 36% and charging.
