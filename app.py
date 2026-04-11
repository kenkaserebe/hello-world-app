# multi-cloud-gitops-platform/hello-world-app/app.py

from flask import Flask
import os

app = Flask(__name__)
@app.route('/')
def hello():
    # Optionally show which cloud (you can pass an env var)
    cloud = os.environ.get('CLOUD', 'unknown')
    return f"Hello from {cloud}!\n"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)