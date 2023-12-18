
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


# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV NAME World

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]



