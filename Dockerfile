
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


FROM python:3.8-slim

WORKDIR /app

RUN python -m venv venv

ENV PATH="/app/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# Command to run your application using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]


