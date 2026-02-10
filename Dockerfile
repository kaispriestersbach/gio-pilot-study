FROM python:3.11-slim

LABEL maintainer="k.spriestersbach@rptu.de"
LABEL description="GIO Pilot Study — Experiment Environment"

# System-Abhaengigkeiten (build-essential fuer spaCy)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python-Abhaengigkeiten zuerst (Docker-Cache-Layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# spaCy-Modelle
RUN python -m spacy download en_core_web_sm && \
    python -m spacy download de_core_news_sm

# Projektdateien kopieren
COPY config.py .
COPY scripts/ scripts/

# Verzeichnisse anlegen
RUN mkdir -p data/raw data/candidates output docs

# Daten- und Output-Verzeichnisse als Volumes (Persistenz)
VOLUME ["/app/data", "/app/output", "/app/docs"]

# Default: interaktive Shell
CMD ["/bin/bash"]
