# Suspend retry after sleep inhibitor: device observation

On 22 November, on the `sleeprefusal1+retry2` GSD package, a controlled `sleep:block` inhibitor was started at 09:13:29 local time. GSD requested suspend and was refused at 09:18:30. While the inhibitor remained active, the retry logged deferred checks rather than repeated suspend requests. The inhibitor ended at 09:25:29; GSD rechecked idle policy at 09:25:30. The kernel recorded `s2idle` entry at 09:30:31 and exit at 09:40:20 after the user returned.

This verifies retry and suspend for this one battery-powered scenario. Screen illumination during the test, user activity during a pending retry, simultaneous inhibitors and other policy transitions require separate device validation. The original failed short observation was inconclusive: Phosh's newly added idle watch appeared to count its timeout again and the user returned before that timeout elapsed.

The local preserved journal has SHA-256 `b3d647a8d78a1783459b630c2f6efac709e97e6342babadc2621b82be85627b9`. It is not included because system journals can contain private information. The test service was inactive at collection and the GSD service was active.

## Activity and screen observation

In a second run, a sleep request was refused at 09:57:50 and retry checks were deferred at 09:58:51 and 10:00:51. The user woke the handset at approximately 10:04 and switched the screen off again. The next pending retry log did not occur; after the test inhibitor ended at 10:07:47, the handset entered s2idle at 10:09:11 and resumed at 10:20:27.

Backlight sampling at approximately 1 Hz recorded 892 zero-brightness samples and one nonzero sample, at 10:04:10, consistent with the user's deliberate wake. This supports absence of longer unsolicited backlight activation during that observation, but does not exclude flashes shorter than the sample interval. The result is consistent with activity cancelling the pending retry; it does not establish all timing races or scenarios. The local brightness log SHA-256 is `aeb539879b90a95ae544834534e5625f9096fc38e71b4a6bf29a3f6b9d8e92b6`.
