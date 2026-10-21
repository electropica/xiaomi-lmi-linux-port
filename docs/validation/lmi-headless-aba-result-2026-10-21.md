# Same-kernel graphical/headless A/B/A — October 21, 2026

The complete three-phase comparison demonstrates no reduction in the gauge-based standby estimate when Phosh and Phoc are stopped. It deprioritizes stopping the graphical session as the next residual-drain intervention; it does not electrically exclude every display/GPU resource.

## Protocol and complete results

One physical unplug was used for three nominal three-minute phases on the same Mobian boot and kernel: graphical session running, session stopped, and session restored. Each phase used the same forced-suspend method, the installed NPU hook and a verified relative RTC endpoint. Radio settings and the normal 900-second automatic-suspend setting were unchanged.

| Phase | Elapsed s | Actual suspension s | Suspension % | Software counter mA | Shadow counter mA | Raw-scale counter mA |
|---|---:|---:|---:|---:|---:|---:|
| graphical-before | 182.123 | 181.252 | 99.522 | 49.87 | 54.18 | 87.39 |
| headless | 181.849 | 181.026 | 99.547 | 51.49 | 53.97 | 90.23 |
| graphical-after | 181.390 | 180.497 | 99.507 | 52.04 | 53.25 | 91.20 |

Both endpoints and all retained cycle samples have USB offline. The headless phase contains no Phosh/Phoc processes; both graphical phases contain one of each. Learned capacity remains 2,686 mAh, and recorded temperature ranges from 21.2 to 21.0 C.

Interpolation between the two graphical software-counter estimates gives 50.97 mA at the headless midpoint, versus 51.49 mA observed headless: a 0.52 mA difference in the opposite direction to a saving. The shadow and raw-scale views also do not show a headless dip below both graphical controls. No statistical significance or precise physical difference is assigned to these small short-window differences.

The reported filtered-current value is still recovering from charging: it moves from -393.441 mA at the first departure endpoint to +11.026 mA at the last endpoint, while the cable is absent. It is therefore not used as the instantaneous or phase-average standby current in this comparison. The three counter methods are related gauge accounting paths, not three independent electrical measurements.

## Conclusion and restoration

The result does not support another graphical-session shutdown test or a GUI change as a demonstrated fix for the persistent sleep estimate. It also cannot distinguish a common gauge-model effect from a shared physical consumer that remains in the same state with or without the compositor. Short post-charge intervals and nonlinear gauge settling remain limits even with the return-to-graphical control.

The observer completed successfully and is inactive. The graphical launcher is active again, the RTC alarm is empty, the NPU recovery state is absent, and the phone charges after reconnection. No firmware, kernel, driver binding, regulator, GPIO or radio configuration was changed.

Private evidence: headless-aba-20261021/events.jsonl, analysis-private.json, return-private.json, source-manifest.json. Raw event-log SHA-256: `a3352a2596d2e84ac195e3d1ca16560b0b47f8b30cb2b1380e54f66144eab556`. Endpoint qualification rejects reconnect contamination, incomplete phases, unexpected graphical processes, invalid timing, changed learned capacity and counter increases; its synthetic guard fixtures pass.
