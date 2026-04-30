// API 配置
export const API_CONFIG = {
  // 开发环境使用Vite代理,生产环境使用环境变量
  BASE_URL: (import.meta as any).env?.VITE_API_BASE_URL || '',
  TIMEOUT: 30000,
}
