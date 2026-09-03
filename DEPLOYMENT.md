# 🚀 MindHue: Deployment, Docker & CI/CD Master Guide

This guide covers deployment across **Vercel** (Frontend SPA), **Render** (Django REST API & Database), **Docker Multi-Container**, and **GitHub Actions CI/CD**.

---

## 🌐 1. Deploy Frontend to Vercel

Vercel provides edge CDN delivery for the React + Vite frontend with automatic HTTPS and SPA routing via `vercel.json`.

### Option A: Via Vercel Web Dashboard (Recommended)
1. Go to [Vercel Dashboard](https://vercel.com/new).
2. Import your GitHub repository: **`AAYU688AAYU/Mindhue-SIH`**.
3. In project settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Add Environment Variable:
   - `VITE_API_URL` = `https://your-mindhue-backend.onrender.com` (Your Render API URL)
5. Click **Deploy**.

### Option B: Via Vercel CLI
```bash
cd frontend
npm i -g vercel
vercel --prod
```

---

## ☁️ 2. Deploy Backend to Render

Render hosts the Django REST API with Gunicorn, WhiteNoise static files, and managed PostgreSQL.

### Option A: Blueprint 1-Click Deploy via `render.yaml` (Recommended)
1. Go to [Render Blueprints](https://dashboard.render.com/blueprints).
2. Connect your GitHub repository: **`AAYU688AAYU/Mindhue-SIH`**.
3. Render will detect `render.yaml` and provision:
   - **Web Service**: `mindhue-backend` (running `build.sh` + Gunicorn)
   - **Managed Database**: `mindhue-postgres` (PostgreSQL 15)
4. Click **Apply**.

### Option B: Manual Web Service Setup on Render
1. Create a **New Web Service** pointing to `AAYU688AAYU/Mindhue-SIH`.
2. Configure:
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`
3. Environment Variables:
   - `PYTHON_VERSION`: `3.10.12`
   - `DJANGO_DEBUG`: `False`
   - `DJANGO_ALLOWED_HOSTS`: `*`
   - `DATABASE_URL`: Your PostgreSQL connection string

---

## 🐳 3. Docker Multi-Container Deployment

Run the complete stack (PostgreSQL + Django API + React Nginx) locally or on any cloud VM using Docker Compose.

### Quick Start with Docker Compose:
```bash
# Build and start all services in detached mode
docker compose up --build -d

# Check running containers
docker compose ps

# View live logs
docker compose logs -f
```

### Services Started:
- 🌐 **Frontend UI**: [http://localhost:5173](http://localhost:5173) (served via Nginx)
- 🔌 **Backend REST API**: [http://localhost:8000/api/](http://localhost:8000/api/) (served via Gunicorn)
- 🗄️ **PostgreSQL Database**: Port `5432` (`mindhue_db`)

### Stop Containers:
```bash
docker compose down
```

---

## 🔄 4. GitHub Actions CI/CD Pipeline

The `.github/workflows/ci-cd.yml` workflow runs automatically on every push or pull request to `main`:

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   Backend CI    │       │   Frontend CI   │       │    Docker CI    │
│  Django Tests   ├──────►│   Vite Build    ├──────►│ Container Build ├──────► Automated Deploy
│  Static Check   │       │   Lint Check    │       │  Image Tests    │      (Vercel & Render)
└─────────────────┘       └─────────────────┘       └─────────────────┘
```

### GitHub Repository Secrets (Optional for Automated Deployment):
In your GitHub repo (`Settings` ➔ `Secrets and variables` ➔ `Actions`):
- `RENDER_DEPLOY_HOOK_URL`: Your Render service deploy hook URL.
- `VERCEL_TOKEN`: Vercel Personal Access Token.
- `VERCEL_ORG_ID`: Vercel Account Org ID.
- `VERCEL_PROJECT_ID`: Vercel Project ID.
