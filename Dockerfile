# Use an official Python runtime as a parent image
FROM python:3.8.3-slim-buster

RUN apt-get update && apt-get install -y libopenslide-dev git

# Copy the current directory contents into the container at /app
RUN git clone https://github.com/gronnesby/histology

WORKDIR /histology

# Install any needed packages specified in requirements.txt
RUN pip3 install --trusted-host pypi.python.org -r requirements.txt

EXPOSE 5000
EXPOSE 80

# Run app.py when the container launches
CMD ["python3", "application.py"]
