SHELL := /bin/bash
UNAME_S := $(shell uname -s)

.PHONY: setup system_deps


setup:
ifeq ($(UNAME_S),Darwin)
	@echo "Detected Darwin. Running system dependencies script..."
	chmod +x Makefiles/darwin/system_dependencies.sh
	./Makefiles/darwin/system_dependencies.sh
	@echo "Setup complete for MacOs"
	

else
	@echo "Detected Windows (or non-Darwin). Checking for Chocolatey..."

	chmod +x Makefiles/windows/system_dependencies.ps1
	./Makefiles/darwin/system_dependencies.sh


	@echo "Setup complete on Windows!"
endif

python_deps: 
	@echo "Making Python Dependencies"
	uv sync

