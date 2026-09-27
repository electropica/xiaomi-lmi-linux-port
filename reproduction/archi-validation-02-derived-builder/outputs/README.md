# Generated outputs (not versioned)

Successful builds publish a raw userdata image and an Android sparse image
under new names here. The scripts refuse to overwrite existing names and keep
timestamped `state-*` evidence beside this directory. Images and states are
external build products, not Git inputs; `.gitignore` excludes them. See the
parent README for the hardware-validated `daily-base` image identities.
