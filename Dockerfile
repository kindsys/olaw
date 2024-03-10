FROM python:3.11-slim

RUN mkdir /app

COPY .env.*example LICENSE poetry.lock pyproject.toml README.md setup.cfg wsgi.py /app/
COPY olaw /app/olaw

WORKDIR /app
ENV PYTHONPATH=${PYTHONPATH}:${PWD}

RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

EXPOSE 5000
CMD ["poetry", "run", "flask", "run", "--host", "0.0.0.0"]