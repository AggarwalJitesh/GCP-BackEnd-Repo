
# FROM google/cloud-sdk:alpine AS builder

# RUN mkdir model
# COPY . /model

# FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

# ENV PYTHONUNBUFFERED True
# ENV APP_HOME /home
# WORKDIR $APP_HOME

# RUN pip install poetry
# COPY poetry.lock pyproject.toml $APP_HOME/

# RUN poetry config virtualenvs.create false 
# RUN poetry install --no-dev
# COPY . $APP_HOME/

# COPY --from=builder /model $APP_HOME/model

# ENV PORT 5000
# ENV CUSTOM_MODEL_PATH="/home/model/distilbert-base-uncased"
# ENV ABSTRACTIVE_MODEL_PATH="/home/model/bart-model"
# ENV MODEL_SERVE="True"

# CMD uvicorn --host 0.0.0.0 --port $PORT main:app


FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]


