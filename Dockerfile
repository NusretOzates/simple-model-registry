FROM python:3.11

WORKDIR /code

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY /app /code/app

CMD ["fastapi", "run", "app/main.py", "--port", "8002"]