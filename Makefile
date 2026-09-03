.PHONY: dev test lint typecheck build up down

dev:
	@echo "Starting development environment..."
	docker compose up

test:
	@echo "Running tests..."
	cd src/backend && pytest
	cd src/frontend && npm test

lint:
	@echo "Running linters..."
	cd src/backend && ruff check .
	cd src/frontend && npm run lint

typecheck:
	@echo "Running type checking..."
	cd src/backend && mypy .
	cd src/frontend && npm run typecheck

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down
