#!/bin/sh
# Install the lmi audio routing into the locations the working handset uses.
#
# Verified against the running system on 2026-11-04 (read-only inspection):
#
#   /etc/pipewire/pipewire.conf.d/99-lmi-audio.conf   root:root 0644
#       System wide PipeWire adapter that creates the S16 speaker sink.
#   /home/mobian/.asoundrc                           mobian:mobian 0644
#       ALSA PCM definitions lmi_speaker / lmi_microphone and the
#       PRI_MI2S_RX hook that routes playback to the ADSP.
#   /usr/share/alsa/ucm2/Xiaomi/lmi/HiFi.conf        root:root 0644
#   /usr/share/alsa/ucm2/conf.d/sm8250/Xiaomi lmi.conf root:root 0644
#       UCM2 profile pair for the Xiaomi lmi codec.
#   /home/mobian/.config/pipewire/pipewire.conf.d/90-lmi-speaker.conf
#   /home/mobian/.config/pipewire/pipewire.conf.d/91-lmi-microphone.conf
#       Per user PipeWire adapters. 90 asks for S32LE, which the AFE refuses,
#       so it is inert; 91 provides the working microphone source.
#
# The two UCM2 files live in a directory owned by the alsa-ucm-conf package.
# They are additions with new names, so dpkg will not overwrite them, but an
# alsa-ucm-conf upgrade may drop the sm8250 directory. The verification step
# re-checks both files after the build.
set -eu

STAGE=/var/lib/lmi-image-staging/lmi-audio
USER_NAME=${1:-mobian}

[ -d "$STAGE" ] || { echo "missing $STAGE" >&2; exit 1; }

install -d -m 0755 /etc/pipewire/pipewire.conf.d
install -m 0644 "$STAGE/99-lmi-audio.conf" /etc/pipewire/pipewire.conf.d/99-lmi-audio.conf

install -d -m 0755 /usr/share/alsa/ucm2/Xiaomi/lmi
install -m 0644 "$STAGE/HiFi.conf" /usr/share/alsa/ucm2/Xiaomi/lmi/HiFi.conf

install -d -m 0755 /usr/share/alsa/ucm2/conf.d/sm8250
install -m 0644 "$STAGE/Xiaomi lmi.conf" "/usr/share/alsa/ucm2/conf.d/sm8250/Xiaomi lmi.conf"

install -d -m 0755 -o "$USER_NAME" -g "$USER_NAME" "/home/$USER_NAME"
install -m 0644 "$STAGE/asoundrc" "/home/$USER_NAME/.asoundrc"
chown "$USER_NAME:$USER_NAME" "/home/$USER_NAME/.asoundrc"

install -d -m 0700 -o "$USER_NAME" -g "$USER_NAME" \
    "/home/$USER_NAME/.config/pipewire/pipewire.conf.d"
for f in 90-lmi-speaker.conf 91-lmi-microphone.conf; do
    if [ -f "$STAGE/$f" ]; then
        install -m 0644 "$STAGE/$f" "/home/$USER_NAME/.config/pipewire/pipewire.conf.d/$f"
        chown "$USER_NAME:$USER_NAME" "/home/$USER_NAME/.config/pipewire/pipewire.conf.d/$f"
    fi
done

echo "LMI_AUDIO_INSTALLED user=$USER_NAME"

# The provenance manifest travels with the overlay; it documents the build,
# it does not belong in the image.
rm -f "$STAGE/manifest.json"
