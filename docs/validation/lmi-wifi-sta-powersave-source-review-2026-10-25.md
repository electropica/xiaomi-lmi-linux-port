# Wi-Fi STA power-save policy: source review — 25 October 2026

This is a host-source review, not a new handset observation or a power fix.
The passive night remains undisturbed. No radio, configuration, firmware,
kernel or package change was performed.

## Question and source identity

Does system suspend force 802.11 station power saving even after a userspace
request disabled it? Inspecting WoW/PCIe DRV alone does not answer that.

Public source revision: a5b3099017ae581aae8bf597b2f9c8c765026af1 in
LineageOS/android_kernel_xiaomi_sm8250. Independently downloaded sources:

| File | SHA256 |
| --- | --- |
| drivers/staging/qcacld-3.0/core/hdd/src/wlan_hdd_power.c | 0f77277c91fb8bee5582c18c0df20fb9e0c4f1e67d409780991b6b24893f7be2 |
| drivers/staging/qcacld-3.0/core/sme/src/common/sme_power_save.c | 74146451d18727598e30af2daef7157b9f1f7d8866251c3d8ca7c1052dd4eafb |
| drivers/staging/qcacld-3.0/components/pmo/core/src/wlan_pmo_suspend_resume.c | 82f26f9fe0afd6a7e47276fb38c445d98c500bdcf11d7a027d50021d15c66ae4 |
| net/wireless/nl80211.c | b0f04a034c3bb0f0bfc6126778eb9df062c3c2f941bda45c4071066187484442 |

## Host chain

- nl80211 SET_POWER_SAVE, lines10351-10381, delegates to set_power_mgmt and
  updates wdev->ps on successful return.
- HDD set_powersave, lines1648-1737, stops the automatic-PS timer. When BMPS is
  enabled it sends SME_PS_ENABLE or SME_PS_DISABLE, or starts the enable timer.
- SME enable check, lines332-363, rejects enable if BMPS is disabled,
  usr_cfg_ps_enable is false, or the session is not associated.
- The private WEXT power command at wlan_hdd_wext.c:4292-4303 explicitly writes
  the SME user flag; the generic cfg80211 callback does not directly write it.
  SME initializes that flag true. These are separate from the wdev->ps cache.
- SME timer flush, lines403-452, applies the enable guards and returns without
  an enable when the timer is not running. HDD suspend calls it at 2024-2034.
  It is therefore not an unconditional STA-PS enable.
- Additional WMA source inspection finds disable at wma_power.c:834-857 calling
  wmi_unified_set_sta_ps(...,false), then updating in_bmps after host submission.
  Normal enable reaches wma_set_force_sleep with enable_ps=true at 762-763.
  Successful host submission is not measured firmware residency.

A no-op timer flush does not establish PS disabled: it may already be active.
WoW preparation adds system/transport/DRV flags and can configure DTIM, then
waits for acknowledgment. Closed firmware can apply behavior not established
by the host sources. Do not assert that PS remains off physically during deep.

The cfg80211 callback also maps disable/enable to start/stop DHCP indications
and a connect runtime-PM hold (HDD 2181-2212,2264-2267). The retained afternoon
shows successful CNSS runtime suspends. That weighs against a simple permanent
connect hold, subject to actual callback paths and wrapper configuration.

## Missing-INI and policy are different hypotheses

The Mobian preparation script links the standard WLAN INI path to the Android
vendor INI and checks readability and final target. The inspected cfg_parse
and qdf_ini_parse chain propagates a failed file read to the HDD startup error
path. A missing whole file is not a demonstrated silent-fallback explanation.

Matching a base INI does not establish matching runtime commands. No active
NetworkManager connection or global power-save value was read during this work.
Do not infer a distribution default.

## Safe next discriminator and its limits

The exact nl80211 GET_POWER_SAVE at 10384-10425 returns wdev->ps. It does not
query hardware, firmware or a driver getter. After preserving the night capture,
one cached read can check whether the generic requested policy is off or on.
It cannot measure radio power or reconstruct the policy selected during deep.
A result of ON cannot rule out private-command, firmware or cache differences.

Do not use a grep of gauge JSONL as a PS-state measurement: it does not contain
general HDD/SME debug logs. The existing scoped kernel retrieval filters many
of those categories, and debug levels may suppress them first. Absence of the
proposed markers is non-discriminating. No logging change was made tonight.

## Decision and contrary evidence

This narrows a possible userspace-policy mechanism; no battery cause is found.
The earlier grouped radio-off trial did not show a robust gain, and the default
SME user flag is true. Both facts weigh against blaming Wi-Fi without actual
policy evidence. No new off trial, power-save setter or kernel patch is justified.

Primary references:
- [Pinned HDD](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/a5b3099017ae581aae8bf597b2f9c8c765026af1/drivers/staging/qcacld-3.0/core/hdd/src/wlan_hdd_power.c)
- [Pinned SME](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/a5b3099017ae581aae8bf597b2f9c8c765026af1/drivers/staging/qcacld-3.0/core/sme/src/common/sme_power_save.c)
- [NetworkManager property contract](https://networkmanager.dev/docs/api/latest/settings-802-11-wireless.html):
  0 global default,1 ignore,2 disable,3 enable. This is the property contract,
  not the handset's current setting.
