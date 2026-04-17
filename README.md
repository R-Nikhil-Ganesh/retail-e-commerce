# dhukan

dhukan is a Cloud Run-ready FastAPI prototype for the AMD Slingshot Ideathon 2026 retail and e-commerce theme. It combines a shopper-facing product page with fit recommendations and review intelligence, plus a retailer dashboard that highlights return risk, root causes, and operational actions.

## Features

- Shopper product page with a live size recommendation flow
- Review intelligence summarization from sample reviews
- Return-risk scoring with a 0-100 score, risk band, reasons, and mitigation advice
- Retailer dashboard with KPI cards, charts, product risk table, and review insights
- Single-container FastAPI app with Jinja templates and static assets
- Cloud Run compatible startup using the `PORT` environment variable

## Architecture

- Backend: FastAPI + Uvicorn
- Templates: Jinja2
- Styling and interaction: HTML, CSS, and vanilla JavaScript
- Runtime data: PostgreSQL (Render)
- Deployment: one container for everything

## Project Structure

- `app/main.py` bootstraps the FastAPI app
- `app/routers/` contains page and API routes
- `app/services/` contains fit, risk, review, and analytics logic
- `app/templates/` contains the server-rendered UI
- `app/static/` contains CSS, JavaScript, and demo images

## Local Setup

1. Create a virtual environment if needed.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set your database URL:

```powershell
$env:DATABASE_URL="postgresql://<username>:<password>@<host>:5432/<database>"
```

4. Run the app:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

5. Open:

- `http://localhost:8080/`
- `http://localhost:8080/product/P001`
- `http://localhost:8080/dashboard`

## Docker

Build the image:

```bash
docker build -t dhukan .
```

Run locally:

```bash
docker run --rm -p 8080:8080 -e PORT=8080 dhukan
```

For PostgreSQL-backed runtime, pass the DB URL as well:

```bash
docker run --rm -p 8080:8080 -e PORT=8080 -e DATABASE_URL="postgresql://<username>:<password>@<host>:5432/<database>" dhukan
```

The container listens on `0.0.0.0` and uses `${PORT:-8080}` so it works on Cloud Run.

## Cloud Run Deployment

Example deploy command:

```bash
gcloud run deploy dhukan \
  --source . \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated
```

If you deploy from a prebuilt container, point `gcloud run deploy` at the image instead of `--source`.

## Notes

- The app requires `DATABASE_URL` and stores app state in PostgreSQL.
- The app expects required keys to already exist in PostgreSQL `app_state`.
- The fit and risk engines are heuristic-based and intended for ideathon-grade explainability.
- The `PORT` environment variable is required on Cloud Run and should not be hardcoded.
