# Family Management Monorepo

This repo now hosts the family management platform as a monorepo:

- `apps/backend`: FastAPI service for all clients
- `apps/web`: Web client
- `apps/miniapp`: WeChat mini program shell

## Architecture

- Web and miniapp share the same FastAPI backend
- Life modules are mounted under `/api/modules/*`
- The mini program is currently a thin shell around the web app, with module-aware routing
- Docker is the default deployment path for NAS and public hosting

## Run locally

Backend:

```bash
python -m uvicorn backend.main:app --app-dir apps --reload
```

Web:

```bash
cd apps/web
npm run dev
```

Mini app:

- open `apps/miniapp` in WeChat DevTools
- set `globalData.webviewUrl` and `globalData.apiBaseUrl` in `apps/miniapp/app.js`

## Docker

Use the root `Dockerfile` and `docker-compose.yml` for NAS or public deployment.

Start:

```bash
docker compose up -d --build
```

App endpoints:

- Web/API: `http://<your-host>:8000`
- Health check: `http://<your-host>:8000/health`

## NAS Deployment

Recommended shape:

1. Put this repo on the NAS
2. Configure `.env`
3. Run `docker compose up -d --build`
4. Use an Nginx Proxy Manager or Synology reverse proxy in front of port `8000`
5. Bind your own domain and enable HTTPS

Persistent data:

- `./data` -> app data
- `./photos` -> uploaded photos

## Public Deployment

For public access, put a reverse proxy in front of the app:

- Nginx
- Caddy
- Traefik
- Synology reverse proxy

You should terminate HTTPS at the proxy and forward traffic to `family-agent:8000`.

## WeChat Mini Program Notes

To embed this into a mini program:

1. Deploy the web app on a public HTTPS domain
2. Add that domain to mini program business domain / request合法域名
3. Set `apps/miniapp/app.js`
4. Open `apps/miniapp` in WeChat DevTools and build

Current miniapp behavior:

- home page opens the main web app
- module center fetches `/api/modules`
- tapping a module opens the corresponding web route in `web-view`

## Suggested Next Steps

- Add a reverse-proxy config example
- Add login/session bridging for miniapp
- Convert high-frequency miniapp pages from `web-view` to native pages one by one
