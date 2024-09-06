# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /

# Install required system packages (including Tabix)
RUN apt-get update \
    && apt-get install

# Install Python dependencies
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# Copy the rest of your application files
COPY . .

# Expose Redis port
#EXPOSE 6379

# Set environment variables
ENV FLASK_APP=App/app.py

# Specify the command to run when the container starts
#CMD service redis-server start && python3 -m flask run --host=82.165.237.220 -p 8003
CMD python3 -m flask run --host=82.165.237.220