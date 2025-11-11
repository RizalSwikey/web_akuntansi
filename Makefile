run-dev:
	uv run manage.py runserver 8001

run-prod:
	uv run manage.py runserver 0.0.0.0:8000

tailwind:
	uv run manage.py tailwind start

mm:
	uv run manage.py makemigrations
	uv run manage.py migrate
	
test:
	uv run manage.py test core

shell:
	uv run manage.py shell

up:
	docker compose up -d

up-build:
	docker compose up -d --build

down: 
	docker compose down

logs:
	docker compose logs django