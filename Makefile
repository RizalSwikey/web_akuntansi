d:
	uv run manage.py runserver

tw:
	uv run manage.py tailwind start

mm:
	uv run manage.py makemigrations
	uv run manage.py migrate
	uv run manage.py runserver
	
test:
	uv run manage.py test core
