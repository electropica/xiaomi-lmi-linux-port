# LMI: drawer and battery gauge follow-up

The customized Phosh drawer's touch-alignment patch was installed and the handset operator confirmed that scrolling and opening applications worked. The drawer still needs larger running-window previews and restoration of the downward closing gesture. The current version provides a back button.

The handset currently runs the project's Linux 7.2.12 lot 9d. The retained charger and gauge patch series records the source changes used for that line of work; the full original source tree has not been recovered and the series alone does not prove a reproducible kernel. Battery percentage and charging behavior need further device validation.

The settings-daemon suspend-refusal fix is installed. Automatic suspend on battery is still blocked when the persistent Wi-Fi reachability inhibitor is active. A sleep inhibitor held by the USB maintenance guard is separate. Power consumption comparisons must record which inhibitors are active.

The gauge's full latch can hold the reported value at 100% while raw MSOC changes. A native-mapping diagnostic candidate is documented separately; it is opt-in and not hardware-validated. The observation of a recent multi-point drop has not yet been explained by the historical samples, which show a gradual 100→99→98→97 transition. Capacity and MSOC readings are sampled separately.
