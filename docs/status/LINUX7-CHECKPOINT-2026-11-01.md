# Linux 7 handset checkpoint — 1 November 2026

This checkpoint summarizes the latest reported handset observations. Older
entries describe their original test dates and must not be read as current
device state. Private logs, images, firmware and device identifiers are not
published here.

## Working and tested

The permanent multi-boot menu retains the Mobian 4.19 and LineageOS recovery
paths. Mobian 7.2.12 has reached a usable Phosh desktop with touch and Wi-Fi.
The application drawer, thumbnail visibility and search closing have received
handset checks. The rear camera preview and flashlight work; the operator
confirmed the lmi4 libcamera rotation correction displays text upright without
mirroring. The 300% display scale is included in the image configuration.

On 31 October a combined test kernel contained the Type-C wake changes and
TFA98XX audio work. The recorded test reports that reconnecting USB woke the
phone from s2idle without a power-key press and that the USB network returned;
it does not establish wake reliability in every sleep scenario or prove deep
hardware residency. The TFA9874 driver bound and its tuning container loaded.
No audible speaker playback is established: audio routing and the full
playback path remain under investigation.

## Remaining work

* The modem/GNSS is not qualified and Maps does not provide a reliable fix.
* The front camera motor and sensor are not yet integrated on Linux 7.
* The charge current limit and USB-PD policy need further work; a battery
  current reading is not an input-current measurement.
* Overnight 31 October–1 November recorded 95% to 58% over approximately
  7 h 22 min, with no increase in the suspend-success counter. This is not a
  suspended-drain measurement. The reported screen state needs rechecking:
  `bl_power=4` alone does not establish an illuminated display. The effect of
  the collector on sleep is not established. Gauge percentage is not a direct
  calibrated electrical consumption measurement.
* The touchscreen, desktop and rear-camera checks do not qualify cellular,
  Bluetooth, audio, front camera, long-term suspend or complete photo/video
  recording.

Host-side candidate sources and build recipes must be reviewed against the
currently installed kernel and its actual artifacts before use. A successful
build or driver probe does not establish safe, audible output. Experimental
results are not a replacement for the retained rescue paths.
