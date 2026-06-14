# Deployment Guide — Spend Sense

Last updated: 2026-06-14

This document is the operational runbook for deploying Spend Sense to production.
Keep it updated whenever the deployment topology changes.

## Architecture

| Layer | Platform | URL |
|-------|----------|-----|
| Frontend | Vercel | `https://spend-sense.vercel.app` |
| Backend API | Render | `https://spend-sense-api.onrender.com` |
| Database | Neon (PostgreSQL 16) | Internal connection string only |
| CI/CD | GitHub Actions | `.github/workflows/` |
| Error monitoring | Sentry (optional) | `https://sentry.io` |
| Backups | GitHub Actions artifact | Weekly, 90-day retention |

---

## Prerequisites

- [ ] GitHub account with push access to `SnehaDagwar/Spend-Sense`
- [ ] Vercel account — [vercel.com/signup](https://vercel.com/signup)
- [ ] Render account — [render.com/register](https://render.com/register)
- [ ] Neon account — [neon.tech](https://neon.tech) (sign in with GitHub for simplicity)
- [ ] Optional: Sentry account — [sentry.io](https://sentry.io)

---

## Step 1 — Neon Database

### 1.1 Create a Neon project

1. Go to [console.neon.tech](https://console.neon.tech) and click **New project**.
2. Settings:
   - **Name**: `spend-sense`
   - **PostgreSQL version**: 16
   - **Region**: AWS ap-south-1 (Mumbai) for lowest latency from India
3. After creation, open the **Connection string** tab.
4. Select driver **psycopg3** and copy the connection string.

The connection string looks like:

```
postgresql+psycopg://username:password@ep-xxx.ap-south-1.aws.neon.tech/neondb?sslmode=require
```

> **Important**: Save this string — you will need it for Render and GitHub secrets.

### 1.2 Enable automated backups

Neon free tier includes **7-day point-in-time restore (PITR)** automatically.
Paid tier extends this to 30 days.

The weekly `pg_dump` workflow in `.github/workflows/db-backup.yml` provides
an additional external backup stored as a GitHub Actions artifact for 90 days.

---

## Step 2 — Backend on Render

### 2.1 Create a Render web service

1. Go to [dashboard.render.com](https://dashboard.render.com) → **New** → **Web Service**.
2. Connect your GitHub account and select `SnehaDagwar/Spend-Sense`.
3. Configure the service:

| Setting | Value |
|---------|-------|
| **Name** | `spend-sense-api` |
| **Root Directory** | `backend` |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Health Check Path** | `/api/v1/health` |
| **Auto-Deploy** | Yes (on push to `main`) |
| **Plan** | Free (or Starter $7/mo for always-on) |

### 2.2 Set environment variables in Render

Go to your service → **Environment** tab and add the following:

| Key | Value | Secret? |
|-----|-------|---------|
| `ENVIRONMENT` | `production` | No |
| `PYTHONPATH` | `.` | No |
| `SECRET_KEY` | *(generated — see below)* | **Yes** |
| `DATABASE_URL` | *(Neon connection string from Step 1)* | **Yes** |
| `BACKEND_CORS_ORIGINS` | `["https://spend-sense.vercel.app"]` | No |
| `OPENAPI_ENABLED` | `false` | No |
| `LOG_LEVEL` | `INFO` | No |
| `AI_PROVIDER` | `mock` | No |
| `SENTRY_DSN` | *(from Sentry project — optional)* | Yes |

**Generating SECRET_KEY** (run locally once):

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 2.3 Add DATABASE_URL as a GitHub secret (for backup workflow)

1. In GitHub → **Settings** → **Secrets and variables** → **Actions**.
2. Create secret `DATABASE_URL` with the same Neon connection string.

### 2.4 Trigger first deploy

Push to `main` or click **Manual Deploy** in the Render dashboard.
Watch the build logs — `alembic upgrade head` will run migrations 0001 and 0002 on the fresh Neon database.

### 2.5 Verify backend

```bash
curl https://spend-sense-api.onrender.com/api/v1/health
```

Expected response:
```json
{
  "status": "ok",
  "version": "0.1.0",
  "environment": "production",
  "db": "ok"
}
```

---

## Step 3 — Frontend on Vercel

### 3.1 Import project

1. Go to [vercel.com/new](https://vercel.com/new) → **Import Git Repository**.
2. Select `SnehaDagwar/Spend-Sense`.
3. Vercel auto-detects Vite. Confirm settings:

| Setting | Value |
|---------|-------|
| **Framework Preset** | Vite |
| **Root Directory** | `.` (repo root) |
| **Build Command** | `npm run build` |
| **Output Directory** | `dist` |

### 3.2 Set environment variables in Vercel

Go to **Settings** → **Environment Variables**:

| Key | Value | Environments |
|-----|-------|--------------|
| `VITE_API_BASE_URL` | `https://spend-sense-api.onrender.com` | Production, Preview |

### 3.3 Deploy

Click **Deploy**. Vercel will build and deploy automatically.

### 3.4 Verify frontend

Open `https://spend-sense.vercel.app` and confirm:
- App loads without console errors
- Network tab shows API calls going to `spend-sense-api.onrender.com`
- Login / register flow works end-to-end

---

## Step 4 — GitHub Actions Secrets

The CI pipeline uses the following GitHub secrets:

| Secret | Used By | Value |
|--------|---------|-------|
| `DATABASE_URL` | `db-backup.yml` | Neon connection string |

Set in: **GitHub** → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.

---

## Step 5 — Custom Domain (Optional)

### Vercel
1. **Settings** → **Domains** → Add `yourdomain.com`
2. Follow the DNS instructions (CNAME or A record via your registrar)

### Render
1. Service → **Settings** → **Custom Domain** → Add `api.yourdomain.com`
2. Add a CNAME record pointing to `spend-sense-api.onrender.com`
3. Update `BACKEND_CORS_ORIGINS` to include the new frontend domain

---

## Rollback Procedure

### Frontend (Vercel)
- Vercel keeps all previous deployments — click **Promote to Production** on any prior deployment in the dashboard.

### Backend (Render)
- Render keeps previous builds — use **Rollback** in the dashboard.
- If a migration is destructive, first downgrade via Alembic:
  ```bash
  # Run from backend/ with correct DATABASE_URL
  alembic downgrade -1
  ```

### Database (Neon PITR)
- In Neon console → **Branches** → **Restore** → Select a timestamp within the 7-day window.
- Create a restore branch, verify data, then promote it.

---

## Monitoring

### Health Check Endpoint

Render polls `/api/v1/health` every 30 seconds. If it returns a non-200 response,
Render restarts the service. The response also includes `"db": "ok"` — you can
alert on `db != "ok"` in an external monitor like [UptimeRobot](https://uptimerobot.com) (free).

### Render Logs

```
Render dashboard → spend-sense-api → Logs
```

Logs are structured JSON in production (via `app.core.logging`), making them
searchable in Render's log viewer.

### Sentry (Optional)

If `SENTRY_DSN` is set, all unhandled exceptions and slow transactions are sent
to Sentry with full stack traces, user context stripped (PII-safe), and
release version tagging.

### GitHub Actions CI Badge

Add to `README.md`:

```markdown
![CI](https://github.com/SnehaDagwar/Spend-Sense/actions/workflows/ci.yml/badge.svg)
```

---

## Environment Variables Reference

### Backend (Render)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENVIRONMENT` | Yes | `local` | Set to `production` on Render |
| `SECRET_KEY` | Yes | — | 48+ char random secret for JWT signing |
| `DATABASE_URL` | Yes | — | Neon PostgreSQL connection string |
| `BACKEND_CORS_ORIGINS` | Yes | `[]` | JSON array of allowed frontend origins |
| `OPENAPI_ENABLED` | No | `true` | Set `false` to hide Swagger in production |
| `LOG_LEVEL` | No | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `SENTRY_DSN` | No | — | Sentry project DSN for error tracking |
| `AI_PROVIDER` | No | `mock` | `gemini`, `openai`, `claude`, or `mock` |
| `GEMINI_API_KEY` | No | — | Required if `AI_PROVIDER=gemini` |
| `OPENAI_API_KEY` | No | — | Required if `AI_PROVIDER=openai` |
| `CLAUDE_API_KEY` | No | — | Required if `AI_PROVIDER=claude` |

### Frontend (Vercel)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_BASE_URL` | Yes | Render backend base URL (no trailing slash) |

---

## Backup Schedule

| Backup Type | Frequency | Retention | Storage |
|-------------|-----------|-----------|---------|
| Neon PITR | Continuous | 7 days (free) | Neon |
| `pg_dump` via GH Actions | Weekly (Sunday 02:00 UTC) | 90 days | GitHub Artifacts |

To restore from a `pg_dump` artifact:
1. Download the `.sql.gz` artifact from GitHub Actions → **Artifacts**
2. Decompress: `gunzip spend_sense_backup_*.sql.gz`
3. Restore: `psql "<NEON_URL>" < spend_sense_backup_*.sql`
