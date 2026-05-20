# Mini App

This is the WeChat mini program shell for the family management system.

It starts as a `web-view` wrapper around the web app, and can later grow native pages for:

- marriage planning
- insurance
- vehicles
- fitness
- family operations

## Production configuration

## Development configuration

The checked-in default is `development` in `config/index.js`:

- `apiBaseUrl`: `http://127.0.0.1:8000`
- `webviewUrl`: `http://127.0.0.1:5173`

When using WeChat DevTools, enable "不校验合法域名、web-view（业务域名）、TLS 版本以及 HTTPS 证书" for local testing.

For real-device preview, `127.0.0.1` points to the phone itself. Change the development URLs to your computer's LAN IP, for example:

- `http://192.168.1.10:8000`
- `http://192.168.1.10:5173`

## Production configuration

Before packaging for release, update `config/index.js`:

- set `ENV` to `production`
- set `production.apiBaseUrl` to the HTTPS API domain
- set `production.webviewUrl` to the HTTPS web app domain

Both domains must be added to the WeChat Mini Program admin console:

- `apiBaseUrl`: request legal domain
- `webviewUrl`: business domain for web-view

The checked-in `famhub.example.com` value is a placeholder. The mini app will show a clear configuration error instead of silently opening an invalid production URL.
