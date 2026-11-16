# Local battery application packages

Run `sh build-debs.sh OUTPUT_DIRECTORY` on an ARM64 Debian/Mobian build host with Rust, Cargo, dpkg and GTK4/Libadwaita development dependencies. The script tests both source trees, builds three separately versioned Debian packages and prints their hashes. It does not install either package, start services, access the phone or read the user’s battery logs. Existing output package names are not overwritten.

The included service uses the existing Mobian account. The viewer depends on the separate logger package. Always back up and verify existing logs and the installed package before a service upgrade. The logger stores locally sampled data only and does not measure hardware deep sleep.

A mocked end-to-end packaging test verified all three output paths and refusal to overwrite. A full isolated native ARM64 build of an earlier two-package version completed on 16 November; the revised three-package recipe still needs an end-to-end ARM64 test. This is not yet part of the clean-image recipe.
