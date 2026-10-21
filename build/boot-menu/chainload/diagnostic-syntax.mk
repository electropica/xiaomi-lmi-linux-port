.PHONY: lmi-diagnostic-syntax
lmi-diagnostic-syntax:
	"$(CC)" $(CC_FLAGS) $(INC) -fno-color-diagnostics -fsyntax-only $(LMI_CHECK_SOURCE)
