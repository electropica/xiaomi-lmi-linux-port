.PHONY: lmi-adapter-syntax
lmi-adapter-syntax:
	"$(CC)" $(CC_FLAGS) $(INC) -fno-color-diagnostics -fsyntax-only /source/edk2-msm/GPLDrivers/Library/SimpleInit/src/linux-boot/aboot.c
