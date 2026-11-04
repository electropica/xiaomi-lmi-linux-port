# Linux 7 status: audio and idle power, 4 November 2026

- On the combined Q6ASM and power-domain candidate, the operator confirmed that two consecutive tracks in Amberol played audibly. This is a functional trial, not comprehensive audio qualification.
- A night unplugged at approximately 86% ended at approximately 50% after reconnection. The exact interval and charge at each cable transition were not captured; these endpoints do not establish an overnight discharge rate or power saving.
- The suspend-boundary collector did not produce a log, and the kernel reported zero successful suspends since boot. The reason for the missing automatic suspend remains unconfirmed.
- A subsequent awake cable-disconnect test recorded both charger and TCPM online values changing from 1 to 0 and UPower `OnBattery` changing from false to true. After reconnection, they returned to 1 and false respectively. This is one awake trial, not proof of correct detection throughout the preceding night or during suspend.
- As a previously tested workaround, the Mobian user was configured to suspend after 900 seconds of inactivity on AC as well as battery. This also permits suspension while a real charger is connected. Its effectiveness on this boot has yet to be measured.
- The keyboard hide button works; keyboard display in Amberol search remains unresolved. Automatic hiding was reverted, and the button was retained.

Battery percentage is an uncalibrated gauge reading, not an energy integral. No 20% reduction is established by these observations.
