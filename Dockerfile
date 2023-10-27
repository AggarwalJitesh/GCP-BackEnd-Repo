# FROM python:3.9-slim-buster

# LABEL python_version="3.9"

# WORKDIR /app

# COPY ./requirements.txt /app/

# RUN pip install -r requirements.txt

# COPY . .

# EXPOSE 5000

# ENV FLASK_APP=app.py

# CMD ["flask", "run", "--host", "0.0.0.0"]


FROM python:3.8

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV NAME World

# Run app.py when the container launches
CMD ["python", "app.py"]



