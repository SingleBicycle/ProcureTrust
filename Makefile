.PHONY: dev test snapshot

dev:
	docker compose -f infra/docker-compose.yml up --build

test:
	@python -c "import importlib.util, subprocess, sys; has = importlib.util.find_spec('pytest') is not None; print('pytest not installed; skipping backend tests') if not has else None; sys.exit(subprocess.call([sys.executable, '-m', 'pytest', 'apps/api']) if has else 0)"
	@if [ -f apps/web/package.json ]; then \
		if command -v npm >/dev/null 2>&1; then \
			(cd apps/web && npm test); \
		else \
			echo "npm not installed; skipping frontend tests"; \
		fi; \
	else \
		echo "apps/web/package.json missing; skipping frontend tests"; \
	fi

snapshot:
	python scripts/snapshot.py
