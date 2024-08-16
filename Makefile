format:
	ruff check --fix

build:
	docker build -t model-registry .

test:
	docker run -it --rm model-registry /bin/bash -c "coverage run -m pytest && coverage report -m"

run:
	docker run -it --rm -p 8000:8002 -e model_storage_path="models" -e model_storage_method="local" -e database_url="sqlite:///database.db"  model-registry