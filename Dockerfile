# Use a specific Python version
FROM python:3.9-slim-buster

# Specify the Python version in a label
LABEL python_version="3.9"

# Set the working directory
WORKDIR /app

# Copy just the requirements file first to leverage Docker cache
COPY ./requirements.txt /app/

# Install requirements
RUN pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Set the Flask app environment variable
ENV FLASK_APP=app.py

# Define the command to run the application
CMD ["flask", "run", "--host", "0.0.0.0"]




