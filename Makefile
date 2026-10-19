.PHONY: install run debug test clean lint lint-strict help

UV := $(shell command -v uv 2>/dev/null || echo "$(HOME)/.local/bin/uv")

check-uv:
	@if ! command -v uv >/dev/null 2>&1 && [ ! -x "$(UV)" ]; then \
		echo "\033[1;33muv no está instalado. Instalando...\033[0m"; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		echo "\033[1;32muv instalado correctamente.\033[0m"; \
	fi

install: check-uv
	@$(UV) sync

# Si no pasan argumentos a make run, usamos config.json por defecto
RUN_ARGS := $(filter-out run --,$(MAKECMDGOALS))
ifeq ($(RUN_ARGS),)
RUN_ARGS := config.json
endif

run:
	@clear
	@$(MAKE) install --no-print-directory
	@echo "\033[1;33m"
	@echo " _____   ___    _____         ___  ___    ___    __   __ "
	@echo "|  _  \ /   \  /  ___|       |   \/   |  /   \  |  \ |  |"
	@echo "| |_)  |  _  \|  |     _____ |  |\/|  | /  _  \ |   \|  |"
	@echo "|   __/  ___  \  |___ |_____||  |  |  |/  ___  \|  |\   |"
	@echo "|__| /__/   \__\_____|       |__|  |__/__/   \__\__| \__|"
	@echo "\033[0m"
	-@uv run python pac-man.py $(RUN_ARGS)
# 	@echo "\033[1;31m"
# 	@echo "\nEND OF PROGRAM - SEE YOU SOON!"
	@echo "\033[0m"
	@$(MAKE) clean --no-print-directory

debug:
	@uv run python -m pdb -m src config.json

clean:
	@rm -rf .mypy_cache .pytest_cache
	@find . -type d -name '__pycache__' -exec rm -rf {} +
	@find . -name '*.pyc' -delete

lint:
	@clear
	@uv run flake8 . --exclude=.venv,data,__pycache__
	@uv run mypy . --exclude "(.venv|data)" --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
	@$(MAKE) clean --no-print-directory

lint-strict:
	@clear
	@uv run flake8 . --exclude=.venv,data,__pycache__
	@uv run mypy . --strict --exclude "(.venv|data)"
	@$(MAKE) clean --no-print-directory

clean_venv: clean
	@rm -rf .venv
	@echo "\033[1;32mEntorno y cachés eliminados. Ejecuta 'make install' para reconstruir.\033[0m"

test:
	@uv run python -m pytest tests/ -v
	@$(MAKE) clean --no-print-directory

help:
	@echo "Usage:"
	@echo "  make install                   # Instala o sincroniza las dependencias"
	@echo "  make run                       # Ejecuta el juego con config.json"
	@echo "  make run -- ruta/config.json   # Ejecuta el juego con otra configuración"
	@echo "  make debug                     # Ejecuta el juego con el depurador pdb"
	@echo "  make test                      # Ejecuta las pruebas"
	@echo "  make clean                     # Elimina cachés y archivos temporales de Python"
	@echo "  make lint                      # Comprueba estilo y tipos"
	@echo "  make lint-strict               # Comprueba estilo y tipos en modo estricto"
	@echo "  make help                      # Muestra esta ayuda"

%:
	@: