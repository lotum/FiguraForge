FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 FORGE_DATA_DIR=/data
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libxrender1 libsm6 libgomp1 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml requirements-tested.txt /app/
COPY backend /app/backend
RUN pip install --no-cache-dir -c requirements-tested.txt -e .
COPY frontend /app/frontend
COPY assets /app/assets
COPY examples/teddy-source.glb /app/examples/teddy-source.glb
COPY scripts/run.py /app/scripts/run.py
RUN useradd --uid 10001 --create-home forge && mkdir /data && chown forge:forge /data
USER forge
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request,os; r=urllib.request.Request('http://127.0.0.1:8000/api/health',headers={'Authorization':'Bearer '+os.environ.get('FORGE_API_TOKEN','')}); urllib.request.urlopen(r,timeout=4)" || exit 1
CMD ["python", "scripts/run.py", "--host", "0.0.0.0", "--port", "8000"]
