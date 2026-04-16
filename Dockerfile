# ── Stage 1: Build React frontend ──────────────────────
FROM node:20-alpine AS frontend
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY index.html vite.config.js ./
COPY src ./src
# API key is baked into the bundle at build time
ARG VITE_API_KEY=change-me
ENV VITE_API_KEY=$VITE_API_KEY
RUN npm run build

# ── Stage 2: FastAPI backend ─────────────────────────
FROM python:3.12-slim
WORKDIR /app

# Install Python deps
RUN pip install --no-cache-dir fastapi uvicorn[standard]

# Copy server + DB snapshot + built frontend
COPY dashboard_server.py ./
COPY comp_data.db ./
COPY --from=frontend /app/dist ./dist

# Auth token — set via `fly secrets set API_KEY=...`
ENV API_KEY=change-me

EXPOSE 5001
CMD ["uvicorn", "dashboard_server:app", "--host", "0.0.0.0", "--port", "5001"]
