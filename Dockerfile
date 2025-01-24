#Create a ubuntu base image with python 3 installed.
FROM python:3.12-slim

#Set the working directory
WORKDIR /

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
#copy all the files
COPY . .

#Install the dependencies
RUN apt-get -y update
RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip install -r requirements.txt

#Expose the required port
EXPOSE 5000

#Run the command
# CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--timeout", "120"]
CMD ["python", "app.py"]
