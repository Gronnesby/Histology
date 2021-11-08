# Use an official Python runtime as a parent image
FROM python:3.10.0-slim-buster

RUN apt-get update && apt-get install -y libopenslide-dev git gcc python3-opencv ffmpeg libsm6 libxext6

# Clone the histology application repository, make sure to pull the correct branch for deployment
RUN git clone --single-branch --branch azure https://github.com/gronnesby/histology

WORKDIR /histology

RUN git submodule update --init --recursive


# Setuptools version > 45 fails with an import error
RUN python3 -m pip install --upgrade setuptools==45
# Install any needed packages specified in requirements.txt
RUN python3 -m pip install --trusted-host pypi.python.org -r requirements.txt

EXPOSE 5000

# Run application.py when the container launches
CMD ["gunicorn", "-w", "12", "--timeout", "600", "--bind", "0.0.0.0:5000", "wsgi:app"]
