FROM python:3.8-slim-buster

# set work directory
ENV APP_HOME /app
WORKDIR $APP_HOME

# allow statements and log message to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED 1

# install dependencies

RUN python3 -m pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# Create a virtual environment (venv) and activate it
# RUN python -m venv venv
# RUN /bin/bash -c "source venv/bin/activate"

# copy project
COPY . .

EXPOSE 8080
ENV PORT 8080
ENV HOST 0.0.0.0


ENTRYPOINT [ "python" "app.py"]
CMD [ "runserver", "0.0.0.0:8080" ]

# CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--timeout", "0", "run:app"]
# CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 run:app



