# Use an official Python runtime as a parent image
FROM ubuntu:16.04

RUN apt-get update && apt-get install -y python3 python3-pip python3-dev libopenslide-dev git

# Copy the current directory contents into the container at /app
RUN git clone https://github.com/gronnesby/histology

WORKDIR /histology

# Install any needed packages specified in requirements.txt
RUN pip3 install --trusted-host pypi.python.org -r requirements.txt

EXPOSE 5000
EXPOSE 80

# Run app.py when the container launches
CMD ["python3", "application.py"]
