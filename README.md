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

- F=README.md; curl --upload-file $F http://localhost:5000/ul/$F
- diff README.md uploads/README.md
- curl http://localhost:5000/dl/README.md
- curl -X POST -F "file=@README.md" http://localhost:5000/ulmp

## Proxy

- curl http://localhost:5000/proxy/dl/README.md
- F=README.md; curl --upload-file $F http://localhost:5000/proxy/ul/$F
- curl -X POST -F "file=@README.md" http://localhost:5000/proxy/ulmp

## Using NGINX reverse proxy

- Edit nginx/conf.d/default.conf
  - set $upstream <your host IP address>:5000;
- docker compose up -d
- curl http://localhost:5001/proxy/dl/README.md
- F=README.md; curl --upload-file $F http://localhost:5001/proxy/ul/$F
- curl -X POST -F "file=@README.md" http://localhost:5001/proxy/ulmp
- (Unlimited client_max_body_size for /proxy)
  - F=1GB; curl --upload-file $F http://localhost:5001/ul/$F
  - 413 Request Entity Too Large
- docker compose down
