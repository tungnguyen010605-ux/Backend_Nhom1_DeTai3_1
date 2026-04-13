FROM python:3.11-slim

WORKDIR /app

# System dependencies for opencv/mediapipe runtime and some build-time wheels.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY Bend/requirements.txt ./Bend/requirements.txt
RUN pip install --no-cache-dir -r Bend/requirements.txt

COPY . .

EXPOSE 8000
ENV PYTHONUNBUFFERED=1
CMD ["uvicorn", "app.main_api:app", "--host", "0.0.0.0", "--port", "8000"]
