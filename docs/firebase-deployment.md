# RAVEN Firebase Deployment & Local Stack Operations

## Docker Compose Production Stack

To start the RAVEN containerized stack backed by Firebase:
```bash
docker compose up -d --build
```

The stack launches:
- `raven-api`: FastAPI backend REST server on port 8000
- `raven-worker`: Background job processing worker
- `raven-dashboard`: Next.js Operations Dashboard on port 3000
- `raven-ngrok`: Ngrok HTTPS tunnel forwarding public requests to `https://<YOUR_NGROK_DOMAIN>.ngrok-free.app`

PostgreSQL and Redis containers have been completely decommissioned and removed from the application architecture.
