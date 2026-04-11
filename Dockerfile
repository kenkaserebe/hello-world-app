# multi-cloud-gitops-platform/hello-world-app/Dockerfile

FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# You can set an environment variable to distiguish clouds in the response
# ENV CLOUD=aws # will be overridden in Kubernetes manifest

CMD ["python", "app.py"]