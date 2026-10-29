# Linux 7 handset status — 29 October 2026

This note records the observed state of the ongoing Poco F2 Pro (`lmi`) work.
It does not imply that the experimental hardware support is complete.

## Rear camera

The rear camera has produced a live preview on Linux 7.2.12. The operator
reported smoother operation comparable to the 4.19 setup and, after installing
the paired experimental libcamera and IPA packages, improved colour and
brightness. The custom sensor gain and AWB changes remain experimental.
Orientation has needed a runtime adjustment, and a previously reported
vertical stripe remains to be checked. The work is not a finished camera
reconstruction recipe.

## Audio and video

A test video and MP3 were created; normal playback could not be demonstrated
with sound. A separate investigation reported that video decoding worked with
a fake audio sink, while no ALSA sound card was available. The ADSP firmware
was subsequently made available on the handset and the WCD codec was reported
bound, but the sound card remained deferred on the TFA9874 speaker link. A
local ADSP boot service was installed during that investigation; its recipe and
persistence need independent review. A proposed device-tree change has not
been validated on the phone. Neither headset nor internal speaker playback is
qualified by these observations.

## GPS and modem

The SDX55M BHI transfer reported success and the hardware execution environment
was observed as secondary bootloader. The host did not progress to a usable
modem or GPS. A proposed MHI event reconciliation patch requires review for
work lifetime, concurrency and power state before a build; a successful SBL
transition would not itself establish mission mode or satellite location.

## Battery and charging

The 28–29 October passive overnight collector did not capture the disconnect
transition and stopped after reconnection. Its endpoint readings were 95% and
71%, with a subsequent recharge included; they are not an electrical energy
measurement. The device reported a long suspended interval, but that interval
does not establish the exact unplugged duration or a calibrated sleep current.

With the camera running while connected to a PC, a battery discharge reading
was observed; charging was later observed after closing the camera. The input
limit was reported as 500 mA, but the actual input current was not measured.
These observations do not quantify camera power or establish a sole cause.

## Interface and packages

The user confirmed the touchscreen drawer scroll, thumbnail rendering and
the drawer's closed-state preview behaviour on the tested Phosh build. A
touchscreen close button and presentation of close confirmation are being
investigated; no tested fix has been installed for that issue. The clipboard
interaction in Text Editor is under separate investigation.

On 29 October, the handset's configured Debian and Mobian repositories were
refreshed and 29 available packages upgraded. The customised Phosh, Phoc and
libcamera packages were retained. Newer Flatpak versions of Amberol,
Calculator, Calendar, Maps, Papers, Text Editor, Weather and Showtime were
also installed alongside their existing Debian versions. Their launcher,
account and application-data integration has not been fully qualified.
