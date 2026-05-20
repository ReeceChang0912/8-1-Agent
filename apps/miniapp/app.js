const { getConfig } = require('./config/index')

App({
  globalData: {
    ...getConfig(),
  },
})
