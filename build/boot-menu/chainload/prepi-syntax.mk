.PHONY: lmi-prepi-syntax
lmi-prepi-syntax:
	"$(CC)" $(CC_FLAGS) $(INC) -fno-color-diagnostics -fsyntax-only /source/edk2-msm/Common/edk2/EmbeddedPkg/Library/PrePiLib/FwVol.c
