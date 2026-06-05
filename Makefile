.PHONY: up down build logs shell-be shell-fe test-be test-fe migrate makemigrations

up:
	docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

down:
	docker-compose down -v

build:
	docker-compose build

logs:
	docker-compose logs -f

shell-be:
	docker-compose exec backend bash

shell-fe:
	docker-compose exec frontend sh

test-be:
	docker-compose exec backend pytest -v

test-fe:
	docker-compose exec frontend npm test

migrate:
	docker-compose exec backend alembic upgrade head

makemigrations:
	docker-compose exec backend alembic revision --autogenerate -m "$(msg)"