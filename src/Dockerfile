FROM python:3.12-alpine
WORKDIR /app
COPY bridge.py /app/bridge.py
USER 65534:65534
CMD ["python", "/app/bridge.py"]
