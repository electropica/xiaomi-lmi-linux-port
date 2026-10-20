# lmi bound-driver coverage inventory — October 20, 2026

This appendix prevents small drivers from disappearing behind broad labels
such as “camera” or “PMIC”. Each row counts live bus entries bound to that
driver, not separate chips. Every row starts as **inventory confirmed**;
its presence here is never a claim that sleep behavior or physical current
has been verified. Evidence and remaining work are tracked in the
[peripheral checklist](lmi-standby-peripheral-checklist-2026-10-20.md).

The retained snapshot has 697 entries over 15 explicitly selected bus
namespaces, 607 bound and 90 without a bound-driver link. Controller, child
interface and logical entries can represent the same hardware. Unbound entries
remain in the private complete inventory; they do not establish absent
hardware or zero power. Firmware-owned/unmodelled devices can be missing
from these Linux lists. This is coverage of the selected software namespaces,
not an assertion that every physical component is inventoried or audited.

| Bus | Entries | Bound | Without driver link |
|---|---:|---:|---:|
| platform | 637 | 567 | 70 |
| i2c | 17 | 10 | 7 |
| spi | 1 | 1 | 0 |
| pci | 2 | 2 | 0 |
| usb | 0 | 0 | 0 |
| spmi | 11 | 10 | 1 |
| soundwire | 4 | 2 | 2 |
| sdw | 0 | 0 | 0 |
| slimbus | 3 | 1 | 2 |
| rpmsg | 7 | 5 | 2 |
| mhi | 4 | 3 | 1 |
| scsi | 11 | 6 | 5 |
| amba | 0 | 0 | 0 |
| virtio | 0 | 0 | 0 |
| mmc | 0 | 0 | 0 |

## Bound driver classes

| Bus | Driver | Bound entries | Evidence level |
|---|---|---:|---|
| i2c | `akm09970` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| i2c | `aw2015_led` | 2 | Inventory confirmed; see checklist for bounded audit evidence |
| i2c | `aw8697_haptic` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| i2c | `bq2597x-charger` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| i2c | `fsa4480-driver` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| i2c | `fts_ts` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| i2c | `i2c_pmic` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| i2c | `nq-nci` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| i2c | `tfa98xx` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| mhi | `diag_mhi_driver` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| mhi | `mhi_uci` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| mhi | `qcom_mhi_qrtr` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| pci | `cnss_pci` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| pci | `pci-msm-rc` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `CAM-FLASH-DRIVER` | 4 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `adsp-loader` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `alarmtimer` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `arm-memlat-mon` | 11 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `arm-smmu` | 2 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `arm_dsu_pmu` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `armv8-pmu` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `audio-ref-clk` | 10 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `audio_apr` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `bcl_pmic5` | 2 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `bimc-bwmon` | 5 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `bolero-clk-rsc-mngr` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `bolero-codec` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `bt_power` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `cam-a5` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `cam-bps` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `cam-cci-driver` | 2 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `cam-cpas` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `cam-csiphy-driver` | 6 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `cam-ipe` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `cam-jpeg-dma` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `cam-jpeg-enc` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `cam_cc-kona` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `cam_fd` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `cam_fd_hw` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `cam_icp` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `cam_isp` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `cam_jpeg` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `cam_req_mgr` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `cam_res_mgr` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `cam_sync` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `cam_vfe` | 4 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `cdsp-loader` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `clk-rpmh` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `cmd-db` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `cnss2` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `cp-qc30` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `cpu_isolate` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `csid_17x` | 2 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `csid_lite` | 2 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `ddr_stats` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `dev_avtimer` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `devbw` | 13 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `devfreq-qcom-fw` | 5 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `devfreq-qcom-qoslat` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `disp_cc-kona` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `drm_dsi_ctrl` | 2 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `dsi_phy` | 2 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `dwc3` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `ext-mdm` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `fastrpc` | 17 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `gcc-kona` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `gdsc` | 25 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `goodix_fp` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `gpi_dma` | 3 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `gpio-keys` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `gpu_cc-kona` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `gsi` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `i2c_geni` | 7 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `ion-msm` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `ipa` | 5 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `ipa_mpm` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `kgsl-3d` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `kgsl-busmon` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `kona-asoc-snd` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `kona-llcc` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `kona-pinctrl` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `kryo_cpu_cache_erp` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `lpm-levels` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `maxim_ds28e16` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `mdss_pll` | 3 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-audio-ion` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-auxpcm-dev` | 6 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-cdc-pinctrl` | 5 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-compress-dsp` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-dai-cdc-dma` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-dai-cdc-dma-dev` | 22 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-dai-fe` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-dai-mi2s` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-dai-q6` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-dai-q6-dev` | 34 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-dai-q6-hdmi` | 3 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-dai-q6-mi2s` | 6 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-dai-q6-spdif` | 4 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-dai-q6-tdm` | 14 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-dai-tdm` | 12 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-dcc` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-dsi-display` | 2 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-dwc3` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-eud` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-ext-disp` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-ext-disp-audio-codec-rx` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-lsm-client` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-pcm-afe` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-pcm-dsp` | 3 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-pcm-dsp-noirq` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-pcm-dtmf` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-pcm-hostless` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-pcm-loopback` | 2 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-pcm-routing` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-pcm-voice` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-restart` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-stub-codec` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-transcode-loopback` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-tsens` | 2 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-usb-hsphy` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm-voip-dsp` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm_bus_device` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm_bus_proxy_client_device` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm_bus_rsc` | 2 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm_cam_cdm` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm_cam_cdm_intf` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm_cam_smmu` | 8 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm_cvp_v4l2` | 7 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm_drm` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm_geni_serial` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm_glink` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm_hdcp` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm_isense_cdsp` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm_lmh_dcvs` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm_mem_dump` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm_notifier` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm_npu` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm_rng` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm_rpm_stat` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm_rpmh_master_stats` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm_sps` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm_vidc_v4l2` | 8 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msm_watchdog` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `msmdrm_smmu` | 2 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `ngd_msm_ctrl` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `npu_cc-kona` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `onewire_gpio` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `pci-msm` | 2 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `q6core_audio` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qce` | 3 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom,actuator` | 2 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom,adc-tm` | 3 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom,camera` | 6 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom,eeprom` | 6 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom,fg-gen4` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom,ois` | 2 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom,pwm-lpg` | 3 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom,qfprom` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom,qnovo5-driver` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom,qpnp-amoled-regulator` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom,qpnp-flash-led-v2` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom,qpnp-pbs` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom,qpnp-power-on` | 4 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom,qpnp-revid` | 3 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom,qpnp-smb5` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom,refgen-regulator` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom,rpmh-regulator` | 47 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom,spmi-pmic-clkdiv` | 3 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom,spmi-sdam` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom,tri-led` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom-cpufreq-hw` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom-llcc-pmu` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom-lpi-pinctrl` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom-smem` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom-spmi-adc5.c` | 3 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom-spmi-gpio` | 4 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom_apcs_ipc` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom_hwspinlock` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom_ice` | 2 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom_ipcc` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcom_smp2p` | 4 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qcrypto` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qmi-cooling-device` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qmi-therm-sensors` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qmp-aop-clk` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qmp_mbox` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qpnp-pdphy` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qsee_ipc_irq_bridge` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qsee_irq` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qseecom` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qsmmuv500-tbu` | 12 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `qupv3_geni_se` | 3 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `ramoops` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `reg-dummy` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `reg-fixed-voltage` | 11 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `rmnet_ipa3` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `rpmh` | 2 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `rtc-pm8xxx` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `rx_macro` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `sde_rsc` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `sde_rsc_rpmh` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `sde_wb` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `sdhci_msm` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `sensors-ssc` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `smcinvoke` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `smp2p_sleepstate` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `snd-soc-dummy` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `spcom` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `spi_geni` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `spmi-temp-alarm` | 3 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `spmi_pmic_arb` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `spss_utils` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `static-map` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `subsys-pil-tz` | 10 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `swr-wcd` | 2 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `system_pm` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `ti,drv8846` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `tx_macro` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `uaudio-qmi` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `ufs_qcom_phy_qmp_v4` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `ufshcd-qcom` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `usb_bam` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `usb_phy_generic` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `usbpd-pm` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `va_macro` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `video_cc-kona` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `voice_mhi_audio` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `wcd938x_codec` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| platform | `xiaomi-touch` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| rpmsg | `apr_tal_rpmsg` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| rpmsg | `mhi,sat_rpmsg` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| rpmsg | `pci-msm-drv` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| rpmsg | `qcom,msm_fastrpc_rpmsg` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| rpmsg | `qcom_smd_qrtr` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| scsi | `sd` | 6 | Inventory confirmed; see checklist for bounded audit evidence |
| slimbus | `btfmslim-driver` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| soundwire | `wcd938x-slave` | 2 | Inventory confirmed; see checklist for bounded audit evidence |
| spi | `ir-spi` | 1 | Inventory confirmed; see checklist for bounded audit evidence |
| spmi | `pmic-spmi` | 10 | Inventory confirmed; see checklist for bounded audit evidence |

Topology evidence SHA-256: `3ee8717bd826dff80e9b7ee6c59af50a477463571b0160fb9244e86470f5950e`.
No raw per-device runtime-status value is promoted to an asleep-state conclusion.
