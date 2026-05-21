const { request } = require('../../utils/request')

function todayString() {
  const date = new Date()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${date.getFullYear()}-${month}-${day}`
}

function normalize(value) {
  return String(value || '').trim()
}

function formatYuan(value) {
  const num = Number(value || 0)
  if (!num) return ''
  return `¥${num.toFixed(0)}`
}

function formatPlainNumber(value, suffix) {
  const num = Number(value || 0)
  if (!num) return ''
  return `${num}${suffix || ''}`
}

function formatDate(value) {
  if (!value) return ''
  const text = String(value)
  const match = text.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (!match) return text
  return `${match[2]}月${match[3]}日`
}

function textField(key, label, placeholder, required) {
  return { key, label, placeholder: placeholder || '', required: !!required, kind: 'text' }
}

function numberField(key, label, placeholder) {
  return { key, label, placeholder: placeholder || '0', kind: 'number' }
}

function dateField(key, label) {
  return { key, label, kind: 'date' }
}

function statusField() {
  return { key: 'status', label: '状态', kind: 'select', required: true }
}

function noteField(key, label, placeholder) {
  return { key, label: label || '备注', placeholder: placeholder || '补充说明、地点、注意事项', kind: 'textarea' }
}

const LIFE_MODULES = [
  {
    id: 'wedding',
    title: '备婚管理',
    shortTitle: '备婚',
    eyebrow: 'Wedding Ops',
    subtitle: '时间线、预算、供应商和待办放在同一个工作面，谁负责、花多少、进度怎样都能直接看清。',
    webRoute: '/modules/wedding',
    apiPath: '/api/modules/wedding',
    typeField: 'item_type',
    primaryKey: 'title',
    noteKeys: ['description'],
    subtitleKeys: ['owner', 'item_date'],
    dateKeys: ['item_date'],
    amountKeys: ['amount', 'planned_amount'],
    tone: 'wedding',
    stats: [
      { key: 'total_items', label: '全部事项' },
      { key: 'todo_count', label: '待办' },
      { key: 'budget_total', label: '预算', format: 'money' },
      { key: 'spent_total', label: '已花', format: 'money' },
    ],
    prompts: [
      { title: '备婚概览', prompt: '/wedding summary', desc: '预算和待办一起看' },
      { title: '新增待办', prompt: '/wedding add 订婚礼摄影', desc: '一句话推进事项' },
      { title: '预算检查', prompt: '/wedding budget', desc: '看预算和实际支出' },
    ],
    types: [
      {
        key: 'timeline',
        label: '时间线',
        hint: '婚礼节点、日期安排、负责人',
        statuses: ['待开始', '进行中', '已完成'],
        fields: [
          textField('title', '事项标题', '例如 试婚纱', true),
          textField('owner', '负责人', '例如 小李'),
          dateField('item_date', '日期'),
          numberField('amount', '金额'),
          statusField(),
          noteField('description'),
        ],
      },
      {
        key: 'budget',
        label: '预算',
        hint: '预算项、计划金额、已支付金额',
        statuses: ['待付款', '部分支付', '已结清'],
        fields: [
          textField('title', '预算项', '例如 婚礼摄影', true),
          numberField('planned_amount', '预算总额'),
          numberField('amount', '已支付'),
          textField('owner', '负责人', '例如 小李'),
          statusField(),
          noteField('description', '说明'),
        ],
      },
      {
        key: 'vendor',
        label: '供应商',
        hint: '联系人、报价、沟通状态',
        statuses: ['待联系', '已沟通', '已签约'],
        fields: [
          textField('title', '供应商', '例如 摄影工作室', true),
          textField('owner', '联系人/负责人', '例如 张经理'),
          numberField('amount', '报价'),
          dateField('item_date', '沟通日期'),
          statusField(),
          noteField('description', '沟通记录'),
        ],
      },
      {
        key: 'todo',
        label: '待办',
        hint: '临近事项、负责人、截止时间',
        statuses: ['待处理', '进行中', '已完成'],
        fields: [
          textField('title', '待办标题', '例如 确认宾客名单', true),
          textField('owner', '负责人', '例如 小李'),
          dateField('item_date', '截止日期'),
          statusField(),
          noteField('description'),
        ],
      },
    ],
  },
  {
    id: 'insurance',
    title: '保险管理',
    shortTitle: '保险',
    eyebrow: 'Family Protection',
    subtitle: '保单、续保提醒和理赔推进放在一起，家庭保障信息不用翻聊天记录。',
    webRoute: '/modules/insurance',
    apiPath: '/api/modules/insurance',
    typeField: 'record_type',
    primaryKey: 'name',
    noteKeys: ['note', 'title'],
    subtitleKeys: ['holder', 'company', 'coverage', 'renew_date'],
    dateKeys: ['renew_date'],
    amountKeys: ['premium', 'amount'],
    tone: 'insurance',
    stats: [
      { key: 'policy_count', label: '保单' },
      { key: 'expiring_count', label: '到期关注' },
      { key: 'annual_premium', label: '年保费', format: 'money' },
      { key: 'claim_amount', label: '理赔', format: 'money' },
    ],
    prompts: [
      { title: '保险概览', prompt: '/insurance list', desc: '查看家庭保单' },
      { title: '续保提醒', prompt: '/insurance renew', desc: '查待续保项目' },
      { title: '理赔推进', prompt: '/insurance claim', desc: '整理理赔状态' },
    ],
    types: [
      {
        key: 'policy',
        label: '保单',
        hint: '保单名称、持有人、保费和续保日',
        statuses: ['有效', '待续保', '已失效'],
        fields: [
          textField('name', '保单名称', '例如 家庭医疗险', true),
          textField('holder', '持有人', '例如 张三'),
          textField('company', '保险公司', '例如 平安保险'),
          textField('coverage', '保障范围', '例如 医疗 / 重疾'),
          numberField('premium', '年保费'),
          dateField('renew_date', '续保日期'),
          statusField(),
          noteField('note'),
        ],
      },
      {
        key: 'reminder',
        label: '提醒',
        hint: '续保、体检、资料补充等提醒',
        statuses: ['待处理', '已安排', '已完成'],
        fields: [
          textField('name', '提醒名称', '例如 医疗险续保', true),
          textField('title', '标题', '例如 提前准备资料'),
          dateField('renew_date', '提醒日期'),
          statusField(),
          noteField('note'),
        ],
      },
      {
        key: 'claim',
        label: '理赔',
        hint: '理赔金额、材料、处理状态',
        statuses: ['准备中', '处理中', '已结案'],
        fields: [
          textField('name', '关联保单', '例如 家庭医疗险', true),
          textField('title', '理赔事项', '例如 门诊报销'),
          numberField('amount', '理赔金额'),
          dateField('renew_date', '日期'),
          statusField(),
          noteField('note', '进展'),
        ],
      },
    ],
  },
  {
    id: 'vehicle',
    title: '车辆管理',
    shortTitle: '车辆',
    eyebrow: 'Vehicle Ledger',
    subtitle: '车辆档案、保养、年检和费用都归档，下一次该做什么不用靠记忆。',
    webRoute: '/modules/vehicle',
    apiPath: '/api/modules/vehicle',
    typeField: 'record_type',
    primaryKey: 'title',
    noteKeys: ['note'],
    subtitleKeys: ['plate', 'model', 'record_date'],
    dateKeys: ['record_date'],
    amountKeys: ['amount', 'mileage'],
    tone: 'vehicle',
    stats: [
      { key: 'vehicle_count', label: '车辆' },
      { key: 'service_count', label: '保养' },
      { key: 'expense_total', label: '费用', format: 'money' },
      { key: 'record_count', label: '记录' },
    ],
    prompts: [
      { title: '车辆概览', prompt: '/vehicle summary', desc: '看车辆状态' },
      { title: '保养提醒', prompt: '/vehicle service', desc: '查下一次保养' },
      { title: '记录费用', prompt: '/vehicle expense 加油 300', desc: '一句话记车费' },
    ],
    types: [
      {
        key: 'vehicle',
        label: '车辆',
        hint: '车牌、车型、当前里程',
        statuses: ['使用中', '待处理', '停用'],
        fields: [
          textField('title', '车辆名称', '例如 家用车', true),
          textField('plate', '车牌', '例如 京A12345'),
          textField('model', '车型', '例如 Model Y'),
          numberField('mileage', '里程'),
          statusField(),
          noteField('note'),
        ],
      },
      {
        key: 'service',
        label: '保养',
        hint: '保养项目、里程、日期',
        statuses: ['待预约', '已预约', '已完成'],
        fields: [
          textField('title', '保养项目', '例如 更换机油', true),
          textField('plate', '车牌', '例如 京A12345'),
          numberField('mileage', '里程'),
          numberField('amount', '费用'),
          dateField('record_date', '日期'),
          statusField(),
          noteField('note'),
        ],
      },
      {
        key: 'expense',
        label: '费用',
        hint: '加油、停车、保险和维修费用',
        statuses: ['待支付', '已支付', '已报销'],
        fields: [
          textField('title', '费用名称', '例如 加油', true),
          textField('plate', '车牌', '例如 京A12345'),
          numberField('amount', '金额'),
          dateField('record_date', '日期'),
          statusField(),
          noteField('note'),
        ],
      },
      {
        key: 'inspection',
        label: '年检',
        hint: '年检、保险、证件到期',
        statuses: ['待处理', '已预约', '已完成'],
        fields: [
          textField('title', '事项', '例如 年检', true),
          textField('plate', '车牌', '例如 京A12345'),
          dateField('record_date', '日期'),
          statusField(),
          noteField('note'),
        ],
      },
    ],
  },
  {
    id: 'fitness',
    title: '健身管理',
    shortTitle: '健身',
    eyebrow: 'Health Routine',
    subtitle: '训练、饮食和身体数据放在一起，适合夫妻或家庭成员一起坚持。',
    webRoute: '/modules/fitness',
    apiPath: '/api/modules/fitness',
    typeField: 'record_type',
    primaryKey: 'title',
    noteKeys: ['note'],
    subtitleKeys: ['record_date', 'duration', 'calories'],
    dateKeys: ['record_date'],
    amountKeys: ['duration', 'calories', 'protein', 'weight'],
    tone: 'fitness',
    stats: [
      { key: 'workout_count', label: '训练' },
      { key: 'meal_count', label: '饮食' },
      { key: 'avg_weight', label: '均重', suffix: 'kg' },
      { key: 'protein_today', label: '蛋白', suffix: 'g' },
    ],
    prompts: [
      { title: '健身概览', prompt: '/fitness summary', desc: '看训练和饮食' },
      { title: '记录训练', prompt: '/fitness workout 跑步30分钟', desc: '一句话记录' },
      { title: '身体数据', prompt: '/fitness metric', desc: '查看趋势' },
    ],
    types: [
      {
        key: 'workout',
        label: '训练',
        hint: '运动项目、时长、消耗',
        statuses: ['计划中', '已完成', '跳过'],
        fields: [
          textField('title', '训练项目', '例如 跑步', true),
          dateField('record_date', '日期'),
          numberField('duration', '时长分钟'),
          numberField('calories', '消耗千卡'),
          statusField(),
          noteField('note'),
        ],
      },
      {
        key: 'meal',
        label: '饮食',
        hint: '餐食、热量、蛋白质',
        statuses: ['已记录', '待补充', '已归档'],
        fields: [
          textField('title', '餐食', '例如 早餐', true),
          dateField('record_date', '日期'),
          numberField('calories', '热量千卡'),
          numberField('protein', '蛋白质克'),
          statusField(),
          noteField('note'),
        ],
      },
      {
        key: 'metric',
        label: '身体',
        hint: '体重、体脂、腰围',
        statuses: ['已记录', '待复测', '已归档'],
        fields: [
          textField('title', '记录标题', '例如 晨起体重', true),
          dateField('record_date', '日期'),
          numberField('weight', '体重kg'),
          numberField('body_fat', '体脂%'),
          numberField('waist', '腰围cm'),
          statusField(),
          noteField('note'),
        ],
      },
    ],
  },
  {
    id: 'documents',
    title: '证件管理',
    shortTitle: '证件',
    eyebrow: 'Document Vault',
    subtitle: '身份证、护照、驾照和家庭证件统一记录，到期提醒不再遗漏。',
    webRoute: '/modules/documents',
    apiPath: '/api/modules/documents',
    typeField: 'doc_type',
    primaryKey: 'title',
    noteKeys: ['note'],
    subtitleKeys: ['holder', 'issuer', 'expiry_date'],
    dateKeys: ['expiry_date', 'issue_date'],
    amountKeys: ['reminder_days'],
    tone: 'documents',
    stats: [
      { key: 'total_count', label: '证件' },
      { key: 'active_count', label: '有效' },
      { key: 'expiring_soon_count', label: '将到期' },
      { key: 'expired_count', label: '已过期' },
    ],
    prompts: [
      { title: '证件列表', prompt: '/documents list', desc: '查看家庭证件' },
      { title: '到期提醒', prompt: '/documents expiring', desc: '查将到期证件' },
      { title: '新增证件', prompt: '/documents add 护照', desc: '一句话归档' },
    ],
    types: [
      {
        key: 'id_card',
        label: '身份证',
        hint: '身份证、签发机关、有效期',
        statuses: ['有效', '即将到期', '已过期'],
        fields: [
          textField('title', '证件名称', '例如 张三身份证', true),
          textField('holder', '持有人', '例如 张三'),
          textField('number', '证件号', '可只填后四位'),
          textField('issuer', '签发机关', ''),
          dateField('issue_date', '签发日期'),
          dateField('expiry_date', '到期日期'),
          numberField('reminder_days', '提前提醒天数'),
          statusField(),
          noteField('note'),
        ],
      },
      {
        key: 'passport',
        label: '护照',
        hint: '护照号、持有人、到期日',
        statuses: ['有效', '即将到期', '已过期'],
        fields: [
          textField('title', '证件名称', '例如 张三护照', true),
          textField('holder', '持有人', '例如 张三'),
          textField('number', '证件号', '可只填后四位'),
          textField('issuer', '签发机关', ''),
          dateField('issue_date', '签发日期'),
          dateField('expiry_date', '到期日期'),
          numberField('reminder_days', '提前提醒天数'),
          statusField(),
          noteField('note'),
        ],
      },
      {
        key: 'license',
        label: '驾照',
        hint: '驾驶证和车辆相关证照',
        statuses: ['有效', '即将到期', '已过期'],
        fields: [
          textField('title', '证件名称', '例如 驾驶证', true),
          textField('holder', '持有人', '例如 张三'),
          textField('number', '证件号', '可只填后四位'),
          textField('issuer', '签发机关', ''),
          dateField('issue_date', '签发日期'),
          dateField('expiry_date', '到期日期'),
          numberField('reminder_days', '提前提醒天数'),
          statusField(),
          noteField('note'),
        ],
      },
      {
        key: 'property',
        label: '房产证',
        hint: '房产、产权和重要证明',
        statuses: ['有效', '待更新', '已归档'],
        fields: [
          textField('title', '证件名称', '例如 房产证', true),
          textField('holder', '持有人', '例如 家庭共有'),
          textField('number', '证件号', '可只填后四位'),
          textField('issuer', '签发机关', ''),
          dateField('issue_date', '签发日期'),
          dateField('expiry_date', '到期日期'),
          numberField('reminder_days', '提前提醒天数'),
          statusField(),
          noteField('note'),
        ],
      },
    ],
  },
  {
    id: 'housing',
    title: '住房管理',
    shortTitle: '住房',
    eyebrow: 'Home Ledger',
    subtitle: '房贷、租金、水电、物业和维修统一看，家庭居住成本更清楚。',
    webRoute: '/modules/housing',
    apiPath: '/api/modules/housing',
    typeField: 'record_type',
    primaryKey: 'title',
    noteKeys: ['note'],
    subtitleKeys: ['location', 'owner', 'due_date'],
    dateKeys: ['due_date'],
    amountKeys: ['amount'],
    tone: 'housing',
    stats: [
      { key: 'total_count', label: '记录' },
      { key: 'utility_count', label: '水电' },
      { key: 'due_soon_count', label: '将到期' },
      { key: 'total_amount', label: '金额', format: 'money' },
    ],
    prompts: [
      { title: '住房概览', prompt: '/housing summary', desc: '看房屋和费用' },
      { title: '维修记录', prompt: '/housing repair', desc: '查报修进度' },
      { title: '费用提醒', prompt: '/housing due', desc: '看将到期账单' },
    ],
    types: [
      {
        key: 'property',
        label: '房产',
        hint: '房屋地址、产权人、状态',
        statuses: ['自住', '出租', '空置'],
        fields: [
          textField('title', '房屋名称', '例如 朝阳家', true),
          textField('location', '地址', '例如 北京朝阳'),
          textField('owner', '产权/负责人', '例如 张三'),
          numberField('amount', '月成本'),
          statusField(),
          noteField('note'),
        ],
      },
      {
        key: 'rent',
        label: '房租',
        hint: '租金、到期日、付款状态',
        statuses: ['待支付', '已支付', '已逾期'],
        fields: [
          textField('title', '费用名称', '例如 5月房租', true),
          textField('location', '地址', ''),
          textField('owner', '负责人', '例如 张三'),
          numberField('amount', '金额'),
          dateField('due_date', '到期日'),
          statusField(),
          noteField('note'),
        ],
      },
      {
        key: 'utility',
        label: '水电',
        hint: '水电燃气、物业和宽带账单',
        statuses: ['待支付', '已支付', '已逾期'],
        fields: [
          textField('title', '账单名称', '例如 电费', true),
          textField('location', '地址', ''),
          numberField('amount', '金额'),
          dateField('due_date', '到期日'),
          statusField(),
          noteField('note'),
        ],
      },
      {
        key: 'repair',
        label: '维修',
        hint: '报修、维修人、费用、状态',
        statuses: ['待处理', '处理中', '已完成'],
        fields: [
          textField('title', '维修事项', '例如 厨房漏水', true),
          textField('location', '位置', '例如 厨房'),
          textField('owner', '负责人', '例如 张三'),
          numberField('amount', '费用'),
          dateField('due_date', '日期'),
          statusField(),
          noteField('note'),
        ],
      },
    ],
  },
  {
    id: 'health',
    title: '健康管理',
    shortTitle: '健康',
    eyebrow: 'Care Timeline',
    subtitle: '体检、用药、复诊和慢病记录集中起来，家庭照护更有连续性。',
    webRoute: '/modules/health',
    apiPath: '/api/modules/health',
    typeField: 'record_type',
    primaryKey: 'title',
    noteKeys: ['note'],
    subtitleKeys: ['provider', 'record_date', 'next_visit'],
    dateKeys: ['record_date', 'next_visit'],
    amountKeys: ['weight', 'bp_systolic', 'bp_diastolic'],
    tone: 'health',
    stats: [
      { key: 'total_count', label: '记录' },
      { key: 'medication_count', label: '用药' },
      { key: 'due_soon_count', label: '复诊' },
      { key: 'abnormal_count', label: '异常' },
    ],
    prompts: [
      { title: '健康概览', prompt: '/health summary', desc: '看家庭健康记录' },
      { title: '用药提醒', prompt: '/health medication', desc: '查用药安排' },
      { title: '复诊计划', prompt: '/health followup', desc: '看近期复诊' },
    ],
    types: [
      {
        key: 'exam',
        label: '体检',
        hint: '体检机构、结论、复查日期',
        statuses: ['正常', '异常', '待复查'],
        fields: [
          textField('title', '体检项目', '例如 年度体检', true),
          textField('provider', '机构', '例如 三甲医院'),
          dateField('record_date', '体检日期'),
          dateField('next_visit', '复查日期'),
          statusField(),
          noteField('note', '结论'),
        ],
      },
      {
        key: 'medication',
        label: '用药',
        hint: '药品、剂量、频率',
        statuses: ['服用中', '已停用', '待补药'],
        fields: [
          textField('title', '药品名称', '例如 维生素D', true),
          textField('dosage', '剂量', '例如 每次1片'),
          textField('frequency', '频率', '例如 每日一次'),
          dateField('record_date', '开始日期'),
          dateField('next_visit', '复诊/复查日期'),
          statusField(),
          noteField('note'),
        ],
      },
      {
        key: 'followup',
        label: '复诊',
        hint: '医院、日期、检查事项',
        statuses: ['待预约', '已预约', '已完成'],
        fields: [
          textField('title', '复诊事项', '例如 牙科复诊', true),
          textField('provider', '机构', '例如 口腔医院'),
          dateField('next_visit', '复诊日期'),
          statusField(),
          noteField('note'),
        ],
      },
      {
        key: 'chronic',
        label: '慢病',
        hint: '指标、体重、血压和备注',
        statuses: ['稳定', '关注', '异常'],
        fields: [
          textField('title', '记录标题', '例如 血压记录', true),
          dateField('record_date', '日期'),
          numberField('weight', '体重kg'),
          numberField('bp_systolic', '收缩压'),
          numberField('bp_diastolic', '舒张压'),
          statusField(),
          noteField('note'),
        ],
      },
    ],
  },
  {
    id: 'travel',
    title: '旅行管理',
    shortTitle: '旅行',
    eyebrow: 'Trip Board',
    subtitle: '行程、预订、预算和打包清单一起管理，家庭出行少漏项。',
    webRoute: '/modules/travel',
    apiPath: '/api/modules/travel',
    typeField: 'record_type',
    primaryKey: 'title',
    noteKeys: ['note'],
    subtitleKeys: ['destination', 'travel_date', 'provider'],
    dateKeys: ['travel_date', 'end_date'],
    amountKeys: ['amount'],
    tone: 'travel',
    stats: [
      { key: 'total_count', label: '记录' },
      { key: 'itinerary_count', label: '行程' },
      { key: 'upcoming_count', label: '近期' },
      { key: 'budget_total', label: '预算', format: 'money' },
    ],
    prompts: [
      { title: '旅行概览', prompt: '/travel summary', desc: '看行程和预算' },
      { title: '打包清单', prompt: '/travel packing', desc: '检查行李' },
      { title: '新增行程', prompt: '/travel add 上海周末游', desc: '一句话创建' },
    ],
    types: [
      {
        key: 'itinerary',
        label: '行程',
        hint: '目的地、同行人、出发和返回',
        statuses: ['计划中', '已预订', '已完成'],
        fields: [
          textField('title', '行程名称', '例如 上海周末游', true),
          textField('destination', '目的地', '例如 上海'),
          textField('companion', '同行人', '例如 全家'),
          dateField('travel_date', '出发日期'),
          dateField('end_date', '返回日期'),
          numberField('amount', '预算'),
          statusField(),
          noteField('note'),
        ],
      },
      {
        key: 'booking',
        label: '预订',
        hint: '酒店、机票、门票和确认状态',
        statuses: ['待预订', '已预订', '已取消'],
        fields: [
          textField('title', '预订项目', '例如 酒店', true),
          textField('destination', '地点', '例如 上海'),
          textField('provider', '平台/供应商', '例如 携程'),
          dateField('travel_date', '日期'),
          numberField('amount', '金额'),
          statusField(),
          noteField('note'),
        ],
      },
      {
        key: 'budget',
        label: '预算',
        hint: '预算项、金额、负责人',
        statuses: ['待确认', '已确认', '已超支'],
        fields: [
          textField('title', '预算项', '例如 餐饮', true),
          textField('destination', '目的地', ''),
          numberField('amount', '金额'),
          statusField(),
          noteField('note'),
        ],
      },
      {
        key: 'packing',
        label: '打包',
        hint: '行李、证件、儿童用品',
        statuses: ['待准备', '已准备', '已装箱'],
        fields: [
          textField('title', '物品', '例如 护照', true),
          textField('companion', '负责人/使用人', '例如 妈妈'),
          dateField('travel_date', '出发日期'),
          statusField(),
          noteField('note'),
        ],
      },
    ],
  },
]

function getModuleConfig(moduleId) {
  return LIFE_MODULES.find((item) => item.id === moduleId) || LIFE_MODULES[0]
}

function getTypeConfig(config, typeKey) {
  return config.types.find((item) => item.key === typeKey) || config.types[0]
}

function getFieldDefault(field, typeConfig, memberName) {
  if (field.key === 'status') return typeConfig.statuses[0] || ''
  if (field.key === 'owner' || field.key === 'holder' || field.key === 'companion') return memberName || ''
  if (field.kind === 'date') return ''
  if (field.kind === 'number') return field.key === 'reminder_days' ? '30' : '0'
  return ''
}

function buildDefaultForm(config, typeKey, memberName) {
  const typeConfig = getTypeConfig(config, typeKey)
  return typeConfig.fields.reduce((form, field) => {
    form[field.key] = getFieldDefault(field, typeConfig, memberName)
    return form
  }, {})
}

function buildFormFromItem(config, typeKey, item, memberName) {
  const typeConfig = getTypeConfig(config, typeKey)
  return typeConfig.fields.reduce((form, field) => {
    const current = item[field.key]
    form[field.key] = current === undefined || current === null || current === ''
      ? getFieldDefault(field, typeConfig, memberName)
      : String(current)
    return form
  }, {})
}

function buildFormFields(config, typeKey, form) {
  const typeConfig = getTypeConfig(config, typeKey)
  return typeConfig.fields.map((field) => {
    const value = normalize(form[field.key])
    const options = field.kind === 'select'
      ? (field.options || typeConfig.statuses.map((status) => ({ label: status, value: status })))
      : []
    const optionIndex = field.kind === 'select'
      ? Math.max(0, options.findIndex((item) => item.value === value))
      : 0
    const option = options[optionIndex] || options[0] || { label: '', value: '' }
    return {
      ...field,
      value,
      index: optionIndex,
      options,
      display_value: field.kind === 'select'
        ? option.label
        : field.kind === 'date'
          ? value || `请选择${field.label}`
          : value,
      is_text: field.kind === 'text',
      is_number: field.kind === 'number',
      is_date: field.kind === 'date',
      is_select: field.kind === 'select',
      is_textarea: field.kind === 'textarea',
    }
  })
}

function buildModuleTabs(currentId) {
  return LIFE_MODULES.map((item) => ({
    id: item.id,
    title: item.shortTitle,
    full_title: item.title,
    active_class: item.id === currentId ? 'active' : '',
    tone_class: `tone-${item.tone}`,
  }))
}

function buildTypeTabs(config, items, activeType) {
  return config.types.map((type) => ({
    key: type.key,
    label: type.label,
    hint: type.hint,
    count: items.filter((item) => normalize(item[config.typeField]) === type.key).length,
    active_class: type.key === activeType ? 'active' : '',
  }))
}

function buildStatsCards(config, stats) {
  return config.stats.map((item) => {
    const raw = stats[item.key]
    const value = item.format === 'money'
      ? formatYuan(raw) || '¥0'
      : `${Number(raw || 0)}${item.suffix || ''}`
    return {
      ...item,
      value,
    }
  })
}

function firstValue(item, keys) {
  for (let i = 0; i < keys.length; i += 1) {
    const value = normalize(item[keys[i]])
    if (value) return value
  }
  return ''
}

function buildAmountChips(config, item) {
  const labels = {
    amount: '金额',
    planned_amount: '预算',
    premium: '保费',
    mileage: '里程',
    duration: '时长',
    calories: '热量',
    protein: '蛋白',
    weight: '体重',
    reminder_days: '提醒',
    bp_systolic: '高压',
    bp_diastolic: '低压',
  }
  const suffixes = {
    mileage: 'km',
    duration: '分钟',
    calories: 'kcal',
    protein: 'g',
    weight: 'kg',
    reminder_days: '天',
    bp_systolic: '',
    bp_diastolic: '',
  }
  return (config.amountKeys || [])
    .map((key) => {
      const value = Number(item[key] || 0)
      if (!value) return ''
      const display = key === 'amount' || key === 'planned_amount' || key === 'premium'
        ? formatYuan(value)
        : formatPlainNumber(value, suffixes[key])
      return `${labels[key] || key} ${display}`
    })
    .filter(Boolean)
}

function buildDateChip(config, item) {
  const key = (config.dateKeys || []).find((name) => normalize(item[name]))
  return key ? formatDate(item[key]) : ''
}

function buildRecordCard(config, item) {
  const typeKey = normalize(item[config.typeField]) || config.types[0].key
  const typeConfig = getTypeConfig(config, typeKey)
  const status = normalize(item.status)
  const note = firstValue(item, config.noteKeys || [])
  const subtitle = (config.subtitleKeys || [])
    .map((key) => {
      const value = normalize(item[key])
      if (!value) return ''
      return key.includes('date') || key === 'renew_date' || key === 'next_visit' ? formatDate(value) : value
    })
    .filter(Boolean)
    .slice(0, 3)
    .join(' · ')
  const chips = [
    typeConfig.label,
    status,
    buildDateChip(config, item),
    ...buildAmountChips(config, item),
  ].filter(Boolean).slice(0, 5)

  return {
    ...item,
    type_key: typeKey,
    type_label: typeConfig.label,
    title_text: normalize(item[config.primaryKey]) || normalize(item.title) || normalize(item.name) || `${typeConfig.label}记录`,
    subtitle_text: subtitle || typeConfig.hint,
    note_text: note || '未填写备注',
    status_text: status || typeConfig.statuses[0] || '未设置',
    chips,
  }
}

function filterRecords(config, items, activeType, keyword) {
  const q = normalize(keyword).toLowerCase()
  return items
    .filter((item) => normalize(item[config.typeField]) === activeType)
    .filter((item) => {
      if (!q) return true
      return Object.keys(item)
        .map((key) => normalize(item[key]).toLowerCase())
        .join(' ')
        .includes(q)
    })
    .map((item) => buildRecordCard(config, item))
    .sort((a, b) => Number(b.id || 0) - Number(a.id || 0))
}

function buildPayload(config, typeKey, form, familyId) {
  const typeConfig = getTypeConfig(config, typeKey)
  const payload = {
    [config.typeField]: typeKey,
    family_id: familyId,
  }
  typeConfig.fields.forEach((field) => {
    const value = form[field.key]
    payload[field.key] = field.kind === 'number' ? Number(value || 0) : normalize(value)
  })
  if (!payload.status) payload.status = typeConfig.statuses[0] || ''
  return payload
}

Page({
  data: {
    loading: true,
    saving: false,
    moduleId: 'wedding',
    moduleTitle: '备婚管理',
    moduleShortTitle: '备婚',
    moduleEyebrow: 'Wedding Ops',
    moduleSubtitle: '',
    moduleToneClass: 'tone-wedding',
    moduleTabs: [],
    typeTabs: [],
    activeType: 'timeline',
    activeTypeLabel: '时间线',
    activeHint: '',
    familyId: '',
    memberName: '',
    items: [],
    visibleRecords: [],
    visibleCountText: '0',
    noVisibleRecords: false,
    stats: {},
    statCards: [],
    searchKeyword: '',
    chatPrompts: [],
    formVisible: false,
    formTitle: '新增记录',
    editingId: '',
    form: {},
    formFields: [],
  },

  onLoad(options) {
    const memberName = wx.getStorageSync('member_name') || ''
    const familyId = wx.getStorageSync('family_id') || ''
    if (!memberName || !familyId) {
      wx.redirectTo({ url: '/pages/auth/auth' })
      return
    }
    this.setData({ memberName, familyId })
    this.applyModule(options.id || 'wedding')
  },

  onShow() {
    if (this.data.familyId) this.refresh()
  },

  applyModule(moduleId) {
    const config = getModuleConfig(moduleId)
    const typeConfig = config.types[0]
    const form = buildDefaultForm(config, typeConfig.key, this.data.memberName)
    wx.setNavigationBarTitle({ title: config.title })
    this.setData({
      loading: true,
      saving: false,
      moduleId: config.id,
      moduleTitle: config.title,
      moduleShortTitle: config.shortTitle,
      moduleEyebrow: config.eyebrow,
      moduleSubtitle: config.subtitle,
      moduleToneClass: `tone-${config.tone}`,
      moduleTabs: buildModuleTabs(config.id),
      activeType: typeConfig.key,
      activeTypeLabel: typeConfig.label,
      activeHint: typeConfig.hint,
      searchKeyword: '',
      chatPrompts: config.prompts,
      items: [],
      visibleRecords: [],
      visibleCountText: '0',
      noVisibleRecords: false,
      stats: {},
      statCards: buildStatsCards(config, {}),
      typeTabs: buildTypeTabs(config, [], typeConfig.key),
      formVisible: false,
      formTitle: `新增${typeConfig.label}`,
      editingId: '',
      form,
      formFields: buildFormFields(config, typeConfig.key, form),
    }, () => this.refresh())
  },

  refresh() {
    const config = getModuleConfig(this.data.moduleId)
    this.setData({ loading: true })
    Promise.all([this.loadItems(config), this.loadStats(config)])
      .then(([items, stats]) => {
        const typeConfig = getTypeConfig(config, this.data.activeType)
        const visibleRecords = filterRecords(config, items, typeConfig.key, this.data.searchKeyword)
        this.setData({
          items,
          stats,
          statCards: buildStatsCards(config, stats),
          typeTabs: buildTypeTabs(config, items, typeConfig.key),
          visibleRecords,
          visibleCountText: String(visibleRecords.length),
          noVisibleRecords: visibleRecords.length === 0,
        })
      })
      .catch(() => {})
      .then(() => this.setData({ loading: false }))
  },

  loadItems(config) {
    return request({
      path: config.apiPath,
      method: 'GET',
      data: { family_id: this.data.familyId },
    }).then((data) => data.items || []).catch(() => [])
  },

  loadStats(config) {
    return request({
      path: `${config.apiPath}/stats`,
      method: 'GET',
      data: { family_id: this.data.familyId },
    }).then((data) => data || {}).catch(() => ({}))
  },

  switchModule(e) {
    const moduleId = e.currentTarget.dataset.id
    if (!moduleId || moduleId === this.data.moduleId) return
    this.applyModule(moduleId)
  },

  switchType(e) {
    const typeKey = e.currentTarget.dataset.key
    const config = getModuleConfig(this.data.moduleId)
    const typeConfig = getTypeConfig(config, typeKey)
    const form = buildDefaultForm(config, typeConfig.key, this.data.memberName)
    const visibleRecords = filterRecords(config, this.data.items, typeConfig.key, this.data.searchKeyword)
    this.setData({
      activeType: typeConfig.key,
      activeTypeLabel: typeConfig.label,
      activeHint: typeConfig.hint,
      typeTabs: buildTypeTabs(config, this.data.items, typeConfig.key),
      visibleRecords,
      visibleCountText: String(visibleRecords.length),
      noVisibleRecords: visibleRecords.length === 0,
      editingId: '',
      formTitle: `新增${typeConfig.label}`,
      form,
      formFields: buildFormFields(config, typeConfig.key, form),
    })
  },

  setSearch(e) {
    const searchKeyword = e.detail.value
    const config = getModuleConfig(this.data.moduleId)
    const visibleRecords = filterRecords(config, this.data.items, this.data.activeType, searchKeyword)
    this.setData({
      searchKeyword,
      visibleRecords,
      visibleCountText: String(visibleRecords.length),
      noVisibleRecords: visibleRecords.length === 0,
    })
  },

  clearSearch() {
    const config = getModuleConfig(this.data.moduleId)
    const visibleRecords = filterRecords(config, this.data.items, this.data.activeType, '')
    this.setData({
      searchKeyword: '',
      visibleRecords,
      visibleCountText: String(visibleRecords.length),
      noVisibleRecords: visibleRecords.length === 0,
    })
  },

  openCreate() {
    const config = getModuleConfig(this.data.moduleId)
    const typeConfig = getTypeConfig(config, this.data.activeType)
    const form = buildDefaultForm(config, typeConfig.key, this.data.memberName)
    this.setData({
      formVisible: true,
      editingId: '',
      formTitle: `新增${typeConfig.label}`,
      form,
      formFields: buildFormFields(config, typeConfig.key, form),
    })
  },

  closeForm() {
    this.setData({ formVisible: false, editingId: '' })
  },

  resetForm() {
    this.openCreate()
  },

  editRecord(e) {
    const id = e.currentTarget.dataset.id
    const item = this.data.items.find((record) => String(record.id) === String(id))
    if (!item) return
    const config = getModuleConfig(this.data.moduleId)
    const typeKey = normalize(item[config.typeField]) || config.types[0].key
    const typeConfig = getTypeConfig(config, typeKey)
    const form = buildFormFromItem(config, typeKey, item, this.data.memberName)
    const visibleRecords = filterRecords(config, this.data.items, typeKey, this.data.searchKeyword)
    this.setData({
      activeType: typeKey,
      activeTypeLabel: typeConfig.label,
      activeHint: typeConfig.hint,
      typeTabs: buildTypeTabs(config, this.data.items, typeKey),
      visibleRecords,
      visibleCountText: String(visibleRecords.length),
      noVisibleRecords: visibleRecords.length === 0,
      formVisible: true,
      editingId: item.id,
      formTitle: `编辑${typeConfig.label}`,
      form,
      formFields: buildFormFields(config, typeKey, form),
    })
  },

  updateFormField(key, value) {
    const config = getModuleConfig(this.data.moduleId)
    const form = {
      ...this.data.form,
      [key]: value,
    }
    this.setData({
      form,
      formFields: buildFormFields(config, this.data.activeType, form),
    })
  },

  setFormInput(e) {
    this.updateFormField(e.currentTarget.dataset.key, e.detail.value)
  },

  changeFormDate(e) {
    this.updateFormField(e.currentTarget.dataset.key, e.detail.value)
  },

  changeFormSelect(e) {
    const key = e.currentTarget.dataset.key
    const field = this.data.formFields.find((item) => item.key === key)
    const index = Number(e.detail.value || 0)
    const option = field && field.options[index] ? field.options[index] : null
    this.updateFormField(key, option ? option.value : '')
  },

  saveRecord() {
    const config = getModuleConfig(this.data.moduleId)
    const typeConfig = getTypeConfig(config, this.data.activeType)
    const missing = this.data.formFields.find((field) => field.required && !normalize(this.data.form[field.key]))
    if (missing) {
      wx.showToast({ title: `请填写${missing.label}`, icon: 'none' })
      return
    }
    this.setData({ saving: true })
    const payload = buildPayload(config, typeConfig.key, this.data.form, this.data.familyId)
    const action = this.data.editingId
      ? request({
          path: `${config.apiPath}/${encodeURIComponent(this.data.editingId)}`,
          method: 'PUT',
          data: payload,
        })
      : request({
          path: config.apiPath,
          method: 'POST',
          data: payload,
        })

    action
      .then((data) => {
        if (data && data.success) {
          wx.showToast({ title: this.data.editingId ? '已更新' : '已添加', icon: 'success' })
          this.closeForm()
          this.refresh()
          return
        }
        wx.showToast({ title: (data && data.message) || '保存失败', icon: 'none' })
      })
      .catch(() => {})
      .then(() => this.setData({ saving: false }))
  },

  removeRecord(e) {
    const id = e.currentTarget.dataset.id
    if (!id) return
    const config = getModuleConfig(this.data.moduleId)
    wx.showModal({
      title: '删除记录',
      content: '确认删除这条记录？',
      confirmText: '删除',
      success: (res) => {
        if (!res.confirm) return
        request({
          path: `${config.apiPath}/${encodeURIComponent(id)}?family_id=${encodeURIComponent(this.data.familyId)}`,
          method: 'DELETE',
        })
          .then((data) => {
            if (data && data.success) {
              wx.showToast({ title: '已删除', icon: 'success' })
              this.refresh()
              return
            }
            wx.showToast({ title: '删除失败', icon: 'none' })
          })
          .catch(() => {})
      },
    })
  },

  openChatPrompt(e) {
    const prompt = e.currentTarget.dataset.prompt || '/modules'
    const title = e.currentTarget.dataset.title || this.data.moduleTitle
    const route = `/chat?prompt=${encodeURIComponent(prompt)}`
    wx.navigateTo({
      url: `/pages/webview/webview?route=${encodeURIComponent(route)}&title=${encodeURIComponent(title)}`,
    })
  },

  openWebModule() {
    const config = getModuleConfig(this.data.moduleId)
    wx.navigateTo({
      url: `/pages/webview/webview?route=${encodeURIComponent(config.webRoute)}&title=${encodeURIComponent(config.title)}`,
    })
  },
})
