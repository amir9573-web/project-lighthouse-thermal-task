FROM python:3.12.10-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OPENBLAS_NUM_THREADS=1
RUN python -m pip install --no-cache-dir --no-deps numpy==2.2.5 scipy==1.15.3
WORKDIR /app
COPY data/ /app/data/
RUN mkdir -p /app/output
