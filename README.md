
# Algal Bloom Monitor (Full Project Scaffold)

This archive contains a full scaffold for the **Algal Bloom Monitor** project:
- backend (Node.js + Express + MongoDB)
- frontend (React) - minimal production-ready scaffold
- ml_model (FastAPI) - minimal prediction microservice
- docker-compose.yml and Dockerfiles for local development

> This scaffold is ready to run locally using Docker Compose. For full production
> hardening (secrets management, rate limits tuning, HTTPS, scaling), follow the
> comments inside each directory.

## Quick start (Docker Compose)
1. Copy `server/.env.example` to `server/.env` and set values (JWT_SECRET, etc).
2. Copy `ml_model/.env.example` to `ml_model/.env` if necessary.
3. From this project root run:
   ```bash
   docker-compose up --build
   ```
4. Backend API: http://localhost:4000
   Frontend (dev server): http://localhost:3000 (if you run it separately)
   ML service: http://localhost:8000/predict

Enjoy — the project is scaffolded to help you expand it further.
