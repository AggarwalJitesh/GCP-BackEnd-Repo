FROM python:3.8-slim-buster

ENV APP_HOME /app
WORKDIR $APP_HOME
# WORKDIR /app

COPY . ./

ENV PYTHONUNBUFFERED 1

RUN python3 -m pip install --upgrade pip
# COPY ./requirements.txt .
RUN pip install -r requirements.txt

# Create a virtual environment (venv) and activate it
# RUN python -m venv venv
# RUN /bin/bash -c "source venv/bin/activate"
# copy project

# COPY . .


# EXPOSE 8080
# ENV PORT 8080
# ENV HOST 0.0.0.0

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app

# ENTRYPOINT [ "python" "app.py"]
# CMD [ "gunicorn", "0.0.0.0:8080" ]

# CMD [ "python" "app.py"]

# CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--timeout", "0", "run:app"]
# CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 run:app



