# FROM python:3.9-slim-buster

# LABEL python_version="3.9"

# WORKDIR /app

# COPY ./requirements.txt /app/

# RUN pip install -r requirements.txt

# COPY . .

# EXPOSE 5000

# ENV FLASK_APP=app.py

# CMD ["flask", "run", "--host", "0.0.0.0"]


# FROM python:3.8

# # Set the working directory to /app
# WORKDIR /app

# # Copy the current directory contents into the container at /app
# COPY . /app

# # Install any needed packages specified in requirements.txt
# RUN pip install --trusted-host pypi.python.org -r requirements.txt

# # Make port 80 available to the world outside this container
# EXPOSE 8080

# # Define environment variable
# ENV FLASK_APP=app.py

# # Run app.py when the container launches
# CMD ["python", "app.py"]

FROM python:3.10.7-slim-buster

# set work directory
ENV APP_HOME /app
WORKDIR $APP_HOME

# allow statements and log message to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip

# Create a virtual environment (venv) and activate it
RUN python -m venv venv
RUN /bin/bash -c "source venv/bin/activate"


COPY ./requirements.txt .
RUN pip install -r requirements.txt


# copy project
COPY . .

EXPOSE 5000

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 run:app



