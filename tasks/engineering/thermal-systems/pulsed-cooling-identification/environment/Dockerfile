FROM python:3.12.10-slim-bookworm@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OPENBLAS_NUM_THREADS=1
RUN python -m pip install --no-cache-dir --no-deps numpy==2.2.5 scipy==1.15.3
WORKDIR /app
COPY data/ /app/data/
RUN mkdir -p /app/output
