#!/usr/bin/env python3
"""Regenerate the linux7 display1 patches from pristine upstream sources.

Host tool. It rebuilds two patches for the lmi Linux 7.2 experiment:

  0002-lmi-dsi-display.patch
      the observer DTS (repository copy) plus the display wiring: panel rails
      (vddio 1.88 V on PM8150 LDO14, vci 3.0 V on PM8150L LDO10, DSI vdda
      1.2 V on PM8150 LDO9), the DSI controller, the 4-lane DSI output and
      the 7 nm PHY, plus the lmi panel node.

  0003-add-msm667uu01-panel.patch
      the lmi AMOLED panel driver (repository copy) and its Kconfig and
      Makefile entries.

The repository copies under kernel/experimental/linux7/ are the source of
truth; this script only produces the diffs that the operator applies to the
pinned kernel tree. It never touches the tree.

Usage:
    python3 regen-display-patches.py [--tree /path/to/linux-v7.2.12-clean]
"""

from __future__ import annotations

import argparse
import difflib
import subprocess
import sys
import tempfile
from pathlib import Path

EXP = Path(__file__).resolve().parent.parent
REPO = EXP.parents[2]
DEFAULT_TREE = (REPO / "output/minimax-kernel7-feasibility/linux-v7.2.12-clean").resolve()

DTS_REPO = EXP / "dts/sm8250-xiaomi-lmi-observer.dts"
DTS_TREE_REL = "arch/arm64/boot/dts/qcom/sm8250-xiaomi-lmi-observer.dts"

PANEL_REPO = EXP / "drivers/gpu/drm/panel/panel-samsung-ams667uu01.c"
PANEL_TREE_REL = "drivers/gpu/drm/panel/panel-samsung-ams667uu01.c"

REGULATORS_OLD = """\t\tvreg_l12a_1p8: ldo12 {
\t\t\tregulator-name = "vreg_l12a_1p8";
\t\t\tregulator-min-microvolt = <1800000>;
\t\t\tregulator-max-microvolt = <1800000>;
\t\t\tregulator-initial-mode = <RPMH_REGULATOR_MODE_HPM>;
\t\t};
\t};
};
"""

REGULATORS_NEW = """\t\tvreg_l12a_1p8: ldo12 {
\t\t\tregulator-name = "vreg_l12a_1p8";
\t\t\tregulator-min-microvolt = <1800000>;
\t\t\tregulator-max-microvolt = <1800000>;
\t\t\tregulator-initial-mode = <RPMH_REGULATOR_MODE_HPM>;
\t\t};

\t\t/*
\t\t * Display rails, lmi display1 variant.
\t\t *
\t\t * vreg_l9a_1p2: DSI controller rail (vdda). PM8150 LDO9 at 1.2 V,
\t\t * same node as the community lmi board (vreg_l9a_1p2).
\t\t */
\t\tvreg_l9a_1p2: ldo9 {
\t\t\tregulator-name = "vreg_l9a_1p2";
\t\t\tregulator-min-microvolt = <1200000>;
\t\t\tregulator-max-microvolt = <1200000>;
\t\t\tregulator-initial-mode = <RPMH_REGULATOR_MODE_HPM>;
\t\t};

\t\t/*
\t\t * vreg_l14a_1p88: panel IO rail (vddio). PM8150 LDO14.
\t\t * The vendor kona-sde-display.dtsi asks for 1880000 uV (unique) and
\t\t * the upstream SM8250 boards declare 1.88 V for the same LDO, while
\t\t * the community lmi board declares 1.8-1.88 V. The vendor value is
\t\t * used because it is the one established for this handset.
\t\t */
\t\tvreg_l14a_1p88: ldo14 {
\t\t\tregulator-name = "vreg_l14a_1p88";
\t\t\tregulator-min-microvolt = <1880000>;
\t\t\tregulator-max-microvolt = <1880000>;
\t\t\tregulator-initial-mode = <RPMH_REGULATOR_MODE_HPM>;
\t\t};
\t};

\t/*
\t * vreg_l10c_3p0: panel VCI rail. PM8150L LDO10 at 3.0 V.
\t * The vendor kona-sde-display.dtsi asks for 3000000 uV (unique); the
\t * community lmi board declares the same rail inside the pm8150l
\t * regulator list.
\t */
\tregulators-1 {
\t\tcompatible = "qcom,pm8150l-rpmh-regulators";
\t\tqcom,pmic-id = "c";

\t\tvreg_l10c_3p0: ldo10 {
\t\t\tregulator-name = "vreg_l10c_3p0";
\t\t\tregulator-min-microvolt = <3000000>;
\t\t\tregulator-max-microvolt = <3000000>;
\t\t\tregulator-initial-mode = <RPMH_REGULATOR_MODE_HPM>;
\t\t};
\t};
};
"""

MDSS_OLD = """&mdss {
\tstatus = "disabled";
};
"""

MDSS_NEW = """&mdss {
\tstatus = "okay";
};

/*
 * DSI display path for the lmi AMOLED panel (display1 variant).
 *
 * Upstream sm8250.dtsi provides mdss (display-subsystem@ae00000),
 * mdss_mdp (display-controller@ae01000), mdss_dsi0 (dsi@ae94000) and
 * mdss_dsi0_phy (phy@ae94400, "qcom,dsi-phy-7nm"). Both mdss and mdss_mdp
 * carry no status property upstream, so enabling &mdss brings the display
 * controller up with it; the observer tree had deliberately disabled it.
 *
 * The DSI controller rail is PM8150 LDO9 (1.2 V). The PHY rail is PM8150
 * LDO5, the same physical rail the USB2 PHY already uses in this tree
 * (declared as vreg_l5a_0p88 above): the community lmi board names it
 * vreg_l5a_0p875, the upstream SM8250 board convention is 880 mV, and the
 * 7 nm PHY driver requests "vdds" without a voltage constraint, so the
 * existing declaration is reused unchanged.
 *
 * The panel node carries the vendor rails (vddio 1.88 V, vci 3.0 V) and the
 * lmi reset line (tlmm 46, active low), as in the community lmi board file.
 */
&mdss_dsi0 {
\tvdda-supply = <&vreg_l9a_1p2>;
\tstatus = "okay";

\tpanel: panel@0 {
\t\tcompatible = "xiaomi,lmi-ams667uu01";
\t\treg = <0>;

\t\tvddio-supply = <&vreg_l14a_1p88>;
\t\tvci-supply = <&vreg_l10c_3p0>;
\t\treset-gpios = <&tlmm 46 GPIO_ACTIVE_LOW>;

\t\tport {
\t\t\tpanel_in: endpoint {
\t\t\t\tremote-endpoint = <&mdss_dsi0_out>;
\t\t\t};
\t\t};
\t};
};

&mdss_dsi0_out {
\tremote-endpoint = <&panel_in>;
\tdata-lanes = <0 1 2 3>;
};

&mdss_dsi0_phy {
\tvdds-supply = <&vreg_l5a_0p88>;
\tstatus = "okay";
};
"""

KCONFIG_OLD = """config DRM_PANEL_SAMSUNG_S6E88A0_AMS427AP24
"""

KCONFIG_NEW = """config DRM_PANEL_SAMSUNG_AMS667UU01
\ttristate "Samsung AMS667UU01 AMOLED DSI panel"
\tdepends on GPIOLIB
\tdepends on OF
\tdepends on DRM_MIPI_DSI
\tdepends on BACKLIGHT_CLASS_DEVICE
\thelp
\t  Say Y or M here if you want to enable support for the
\t  Samsung AMS667UU01 DDIC and connected MIPI DSI panel.
\t  Currently supported panels:

\t    Xiaomi j11 38 08 0a FHD panel
\t    (found in the Xiaomi POCO F2 Pro / Redmi K30 Pro, board lmi)

config DRM_PANEL_SAMSUNG_S6E88A0_AMS427AP24
"""

MAKEFILE_ANCHOR = "obj-$(CONFIG_DRM_PANEL_SAMSUNG_S6D7AA0) += panel-samsung-s6d7aa0.o\n"
MAKEFILE_NEW = (
    "obj-$(CONFIG_DRM_PANEL_SAMSUNG_AMS667UU01) += panel-samsung-ams667uu01.o\n"
    + MAKEFILE_ANCHOR
)


def replace_once(text: str, old: str, new: str, what: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"anchor for {what} matched {count} times, expected 1")
    return text.replace(old, new)


def diff(old: str, new: str, rel: str) -> str:
    lines = difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=f"a/{rel}",
        tofile=f"b/{rel}",
        n=3,
    )
    return "".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tree", default=str(DEFAULT_TREE))
    parser.add_argument("--check", action="store_true",
                        help="only verify that the committed patches still match")
    args = parser.parse_args()

    tree = Path(args.tree).resolve()
    if not (tree / "drivers/gpu/drm/panel/Kconfig").is_file():
        raise SystemExit(f"pristine tree looks wrong: {tree}")
    if not DTS_REPO.is_file():
        raise SystemExit(f"observer DTS not found: {DTS_REPO}")

    dts_old = DTS_REPO.read_text()
    dts_new = replace_once(dts_old, REGULATORS_OLD, REGULATORS_NEW, "rails")
    dts_new = replace_once(dts_new, MDSS_OLD, MDSS_NEW, "display nodes")

    kconfig_old = (tree / "drivers/gpu/drm/panel/Kconfig").read_text()
    kconfig_new = replace_once(kconfig_old, KCONFIG_OLD, KCONFIG_NEW, "Kconfig")

    makefile_old = (tree / "drivers/gpu/drm/panel/Makefile").read_text()
    makefile_new = replace_once(makefile_old, MAKEFILE_ANCHOR, MAKEFILE_NEW, "Makefile")

    panel_new = PANEL_REPO.read_text()
    panel_old = ""

    patch2 = (
        f"Subject: [PATCH 2/3] lmi: add the DSI display path to the observer DTS\n"
        f"\n"
        f"Enable the upstream SM8250 display subsystem, the DSI controller, the\n"
        f"4-lane DSI output, the 7 nm PHY and the lmi AMOLED panel node, and\n"
        f"declare the three panel rails that the observer tree did not carry\n"
        f"(vddio 1.88 V on PM8150 LDO14, vci 3.0 V on PM8150L LDO10 and the\n"
        f"DSI controller rail 1.2 V on PM8150 LDO9).\n"
        f"\n"
        f"Generated by kernel/experimental/linux7/tools/regen-display-patches.py.\n"
        f"---\n"
        + diff(dts_old, dts_new, DTS_TREE_REL)
    )

    patch3 = (
        f"Subject: [PATCH 3/3] drm/panel: add the lmi AMOLED panel driver\n"
        f"\n"
        f"Add the Samsung AMS667UU01 panel driver used by the Xiaomi POCO F2 Pro\n"
        f"(board lmi), on the Linux 7.2 DRM panel API. The driver controls the\n"
        f"panel rails itself (vddio 1.88 V, vci 3.0 V) and sends the vendor DCS\n"
        f"power-on sequence instead of relying on the bootloader state.\n"
        f"\n"
        f"Generated by kernel/experimental/linux7/tools/regen-display-patches.py.\n"
        f"---\n"
        + diff(kconfig_old, kconfig_new, "drivers/gpu/drm/panel/Kconfig")
        + diff(makefile_old, makefile_new, "drivers/gpu/drm/panel/Makefile")
        + diff(panel_old, panel_new, PANEL_TREE_REL)
    )

    out2 = EXP / "patches/0002-lmi-dsi-display.patch"
    out3 = EXP / "patches/0003-add-msm667uu01-panel.patch"
    if args.check:
        for path, text in ((out2, patch2), (out3, patch3)):
            if not path.is_file():
                raise SystemExit(f"missing committed patch: {path}")
            if path.read_text() != text:
                raise SystemExit(f"committed patch is stale: {path}")
        print("PATCHES_UP_TO_DATE")
        return 0

    out2.write_text(patch2)
    out3.write_text(patch3)
    print("PATCHES_WRITTEN", out2, out3)
    return 0


if __name__ == "__main__":
    sys.exit(main())
