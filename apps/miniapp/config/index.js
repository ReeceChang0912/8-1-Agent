// development: 微信开发者工具本地调试
// production: 上线前必须替换为真实 HTTPS 域名
const ENV = 'development'

const envConfig = {
  development: {
    apiBaseUrl: 'http://127.0.0.1:8000',
    webviewUrl: 'http://127.0.0.1:5173',
  },
  production: {
    apiBaseUrl: 'https://famhub.example.com',
    webviewUrl: 'https://famhub.example.com',
  },
}

const PLACEHOLDER_HOSTS = ['your-domain.example.com', 'famhub.example.com']

function trimTrailingSlash(url) {
  return String(url || '').replace(/\/+$/, '')
}

function getConfig() {
  const config = envConfig[ENV] || envConfig.production
  return {
    env: ENV,
    apiBaseUrl: trimTrailingSlash(config.apiBaseUrl),
    webviewUrl: trimTrailingSlash(config.webviewUrl),
    defaultRoute: '/',
  }
}

function isPlaceholderUrl(url) {
  return PLACEHOLDER_HOSTS.some((host) => String(url || '').includes(host))
}

module.exports = {
  getConfig,
  isPlaceholderUrl,
}
