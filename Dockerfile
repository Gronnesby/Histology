# Use an official Python runtime as a parent image
FROM python:3.8.3-slim-buster

RUN apt-get update && apt-get install -y libopenslide-dev git gcc

# Clone the histology application repository, make sure to pull the correct branch for deployment
RUN git clone --single-branch --branch azure https://github.com/gronnesby/histology
WORKDIR /histology

# Create a virual environment in the workdir
RUN pip3 install virtualenv
RUN python -m virtualenv .
RUN source bin/activate

# Setuptools version > 45 fails with an import error
RUN pip3 install --upgrade setuptools==45
# Install any needed packages specified in requirements.txt
RUN pip3 install --trusted-host pypi.python.org -r requirements.txt

EXPOSE 80

# Run application.py when the container launches
CMD ["gunicorn", "--timeout", "600", "--bind", "0.0.0.0:80", "wsgi:APP"]
