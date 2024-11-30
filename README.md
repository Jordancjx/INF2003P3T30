# INF2003P3T30

## How to run

Make sure you have pip installed and have a virtual environment setup

## Load Docker.tar image file
docker load -i flask_app.tar 

## Run Docker instance
docker run -d -p 5000:5000 flask  

## Access the application via localhost:5000
