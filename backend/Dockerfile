FROM python:3.12-slim

WORKDIR /app

# System deps for any C-extension wheels
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Install Python deps first (better layer cache). Use the BACKEND requirements,
# which has fastapi/uvicorn/sqlalchemy -- the root requirements.txt does not.
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend app, shared modules, and root config.py (build context = repo root)
COPY backend/ ./backend/
COPY modules/ ./modules/
COPY config.py ./config.py

# Run from backend/ so uvicorn app.main:app resolves the app package
WORKDIR /app/backend
RUN mkdir -p /app/backend/data

ENV PYTHONUNBUFFERED=1
# Absolute SQLite path (four slashes = absolute) inside the container
ENV NUTRIVISION_DB=sqlite:////app/backend/data/nutrivision.db

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
