# State excluded from reproduction

The following must be absent, cleared, regenerated on first boot, or supplied
out of band. They are not lock inputs:

- `/etc/machine-id` contents;
- password databases, password hashes, PINs and keyrings;
- private keys, SSH authorized keys and SSH host keys;
- NetworkManager connection profiles, SSIDs, PSKs and other network secrets;
- personal DConf databases and per-user application state;
- browser, Chatty, GNOME and application profiles;
- journals, logs, coredumps, crash data and pstore data;
- caches, thumbnails, temporary files and downloaded data;
- `/run`, process state, sockets, PIDs and transient seat/session state;
- generated DHCP, NTP, rfkill and NetworkManager runtime state;
- shell histories and terminal scrollback;
- phone serial numbers, account tokens and device-specific credentials.

The `mobian` account identity (UID/GID 1000) and required group memberships
are part of the structural contract. Its authentication material is not.

The current builder's credential and SSH-key injection must be removed or
made an explicit, external first-boot step before it is used as a sanitized
reproduction recipe.
