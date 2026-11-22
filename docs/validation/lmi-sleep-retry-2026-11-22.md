# Suspend retry after sleep inhibitor: device observation

On 22 November, on the `sleeprefusal1+retry2` GSD package, a controlled `sleep:block` inhibitor was started at 09:13:29 local time. GSD requested suspend and was refused at 09:18:30. While the inhibitor remained active, the retry logged deferred checks rather than repeated suspend requests. The inhibitor ended at 09:25:29; GSD rechecked idle policy at 09:25:30. The kernel recorded `s2idle` entry at 09:30:31 and exit at 09:40:20 after the user returned.

This verifies retry and suspend for this one battery-powered scenario. Screen illumination during the test, user activity during a pending retry, simultaneous inhibitors and other policy transitions require separate device validation. The original failed short observation was inconclusive: Phosh's newly added idle watch appeared to count its timeout again and the user returned before that timeout elapsed.

The local preserved journal has SHA-256 `b3d647a8d78a1783459b630c2f6efac709e97e6342babadc2621b82be85627b9`. It is not included because system journals can contain private information. The test service was inactive at collection and the GSD service was active.
