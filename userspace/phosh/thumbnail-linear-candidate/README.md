# Linear application thumbnails for lmi

Candidate backport of Phoc upstream commit [a19515c8ed4abea0e9a5dab324466a88370a3a50](https://gitlab.gnome.org/World/Phosh/phoc/-/commit/a19515c8ed4abea0e9a5dab324466a88370a3a50), `render: Use linear modifier`, March 28, 2025.

The observed overview thumbnail is visibly striped while the complete screenshot is readable. Installed Phoc is 0.46.0-1+lmishelldnd1 using GLES2 via Zink/Turnip. Its thumbnail render target requests DRM_FORMAT_MOD_INVALID. Upstream replaces this with DRM_FORMAT_MOD_LINEAR, explicitly noting trouble with Vulkan and the intended linear layout. This is a supported candidate cause, not yet a proven device fix.

The recipe modifies only that allocation modifier plus Debian changelog, retains the qualified cursor source for home drag/drop, and preserves the existing package as rollback. Phosh ESR quiet packages and the temporary FG kernel are untouched by the build. Default invocation validates sources and rollback only. `sudo python3 build-packages.py --execute` performs the user-launched incremental package build with upstream tests in a private mount namespace. No network dependency upgrade, phone contact, installation, kernel or image build occurs.

An interrupted source/changelog preparation is rejected for inspection. The candidate still requires guarded installation, a compositor/session restart (not a handset reboot), fresh thumbnail capture, and confirmation that home drag/drop still works. Do not promote complete-image pins until those checks pass.

## Actual device outcome, October 24

The package was built and installed. A fresh post-RTC-test screenshot still shows striped cards while surrounding output is readable. The linear-modifier backport alone did not fix this symptom. The next [row-readback candidate](../thumbnail-row-readback-candidate/README.md) is host-tested only and retains this package as rollback. Do not mark either as a verified device thumbnail fix.
