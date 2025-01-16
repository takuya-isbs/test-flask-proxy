# test-flask-proxy

## Setup

- (install venv)
  - ex. sudo apt install python3.10-venv
- python3 -m venv venv
- source venv/bin/activate
- pip install -r requirements.txt

## Start server

- source venv/bin/activate
- mkdir uploads
- python app.py

## Upload and Download

- curl --upload-file README.md http://localhost:5000/ul/README.md
- diff README.md uploads/README.md
- curl http://localhost:5000/dl/README.md
- curl -X POST -F "file=@README.md" http://localhost:5000/ulmp

## Proxy

- curl http://localhost:5000/proxy/dl/README.md
- curl --upload-file README.md http://localhost:5000/proxy/ul/README.md
- curl -X POST -F "file=@README.md" http://localhost:5000/proxy/ulmp
