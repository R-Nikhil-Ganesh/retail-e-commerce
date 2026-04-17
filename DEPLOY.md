# Deployment to Google Cloud Run

## Prerequisites

1. **Google Cloud Project**: Create a project at [console.cloud.google.com](https://console.cloud.google.com)
2. **gcloud CLI**: Install from [cloud.google.com/sdk](https://cloud.google.com/sdk)
3. **Docker**: Installed locally (for local testing)
4. **Permissions**: Ensure you have `roles/run.admin` and `roles/storage.admin` roles

## Local Testing

Test the Docker image locally before deploying:

```bash
# Build the image
docker build -t dhukan:latest .

# Set environment variables
$env:DATABASE_URL='postgresql://your_user:your_password@your_host:5432/your_db'

# Run the container
docker run -p 8080:8080 `
  -e DATABASE_URL=$env:DATABASE_URL `
  dhukan:latest

# Test the endpoints
# Health check: http://localhost:8080/healthz
# API endpoints: http://localhost:8080/api/...
```

## Deployment Steps

### Option 1: Manual Deployment (One-time)

1. **Authenticate with Google Cloud**:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Build and push image to Container Registry**:
   ```bash
   $env:PROJECT_ID=$(gcloud config get-value project)
   
   docker build -t gcr.io/$env:PROJECT_ID/dhukan:latest .
   docker push gcr.io/$env:PROJECT_ID/dhukan:latest
   ```

3. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy dhukan `
     --image gcr.io/$env:PROJECT_ID/dhukan:latest `
     --platform managed `
     --region asia-south1 `
     --allow-unauthenticated `
     --set-env-vars DATABASE_URL='YOUR_DATABASE_URL' `
     --memory 512Mi `
     --cpu 1 `
     --timeout 3600
   ```

### Option 2: Automated Deployment (CI/CD with Cloud Build)

1. **Push code to Cloud Source Repository or GitHub**:
   ```bash
   git remote add google https://source.developers.google.com/p/YOUR_PROJECT_ID/r/dhukan
   git push google main
   ```

2. **Set up Cloud Build trigger**:
   - Go to Cloud Console → Cloud Build → Triggers
   - Connect your repository
   - Create a trigger that runs on push to main branch
   - The `cloudbuild.yaml` file will automatically execute

3. **Configure substitutions** in Cloud Build:
   - In the trigger settings, add substitution variable:
     - `_DATABASE_URL`: Your PostgreSQL connection string

## Checking Deployment Status

```bash
# View logs
gcloud run logs read dhukan --region asia-south1

# Get service details
gcloud run services describe dhukan --region asia-south1

# Get the service URL
gcloud run services describe dhukan --region asia-south1 --format='value(status.url)'
```

## Testing the Deployed Service

```bash
$env:SERVICE_URL=$(gcloud run services describe dhukan --region asia-south1 --format='value(status.url)')

# Health check
$env:SERVICE_URL/healthz

# API endpoints
$env:SERVICE_URL/api/products
$env:SERVICE_URL/api/profile
```

## Environment Variables

Set the following environment variables in Cloud Run:

- `DATABASE_URL`: PostgreSQL connection string

## Important Notes

- **Port**: Cloud Run automatically sets the `PORT` environment variable. The Dockerfile correctly uses `${PORT:-8080}`
- **Health Checks**: Cloud Run sends requests to `/` by default. The app responds at `/healthz` - ensure this endpoint is accessible
- **Memory**: Start with 512Mi; adjust based on performance
- **Concurrency**: Cloud Run defaults to 80 concurrent requests per instance
- **Cold starts**: Python apps may have slower cold starts; use minimum instances if needed

## Troubleshooting

**Service won't start**:
- Check logs: `gcloud run logs read dhukan --region asia-south1`
- Verify `DATABASE_URL` environment variable is set
- Ensure Dockerfile exposes correct port (8080)

**Database connection fails**:
- Verify `DATABASE_URL` format: `postgresql://user:password@host:port/db`
- Check if database allows connections from Cloud Run IP ranges
- Consider using Cloud SQL Proxy for managed databases

**Health checks failing**:
- Ensure `/healthz` endpoint is accessible and returns status 200
- Check startup time - increase Cloud Run timeout if needed

## Monitoring

- **Cloud Monitoring**: Set up metrics dashboard in Cloud Console
- **Cloud Logging**: View application logs
- **Cloud Trace**: Track request latency
- **Error Reporting**: Automatic error detection and reporting
