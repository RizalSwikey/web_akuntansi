run:
	uv run manage.py runserver

tailwind:
	uv run manage.py tailwind start

mm:
	uv run manage.py makemigrations
	uv run manage.py migrate
	
test:
	uv run manage.py test core

shell:
	uv run manage.py shell

