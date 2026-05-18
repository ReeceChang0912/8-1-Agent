"""
工作台数据服务
聚合新闻、天气、节假日等信息
"""
import requests
import json
import re
import random
import os
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from urllib.parse import quote

# ===== 天气 (中国天气网 + 和风天气) =====

CITY_CODE_MAP = {
    '北京': '101010100', '上海': '101020100', '广州': '101280101',
    '深圳': '101280601', '杭州': '101210101', '成都': '101270101',
    '武汉': '101200101', '西安': '101110101', '南京': '101190101',
    '重庆': '101040100', '天津': '101030100', '苏州': '101190401',
    '昆明': '101290101',
}


def fetch_weather(city: str = "昆明") -> Dict:
    """获取天气信息（真实数据优先）"""
    result = _fetch_qweather(city)
    if result:
        return result

    result = _fetch_weather_china(city)
    if result:
        return result

    result = _fetch_weather_wttr(city)
    if result:
        return result

    return _mock_weather(city)


def _fetch_qweather(city: str) -> Optional[Dict]:
    """和风天气 API（需配置 QWEATHER_API_KEY）"""
    api_key = os.environ.get('QWEATHER_API_KEY', '')
    if not api_key:
        return None
    try:
        code = CITY_CODE_MAP.get(city, '101020100')
        loc = code[-9:] if len(code) > 9 else code[-6:]
        # 当前天气
        now_url = f'https://devapi.qweather.com/v7/weather/now?location={loc}&key={api_key}'
        now_resp = requests.get(now_url, timeout=10)
        if now_resp.status_code != 200:
            return None
        now_data = now_resp.json()
        if now_data.get('code') != '200':
            return None
        now = now_data.get('now', {})

        # 3天预报
        fc_url = f'https://devapi.qweather.com/v7/weather/3d?location={loc}&key={api_key}'
        fc_resp = requests.get(fc_url, timeout=10)
        fc_days = []
        if fc_resp.status_code == 200:
            fc_data = fc_resp.json()
            if fc_data.get('code') == '200':
                fc_days = [
                    {
                        'date': day.get('fxDate', ''),
                        'temp_high': day.get('tempMax', ''),
                        'temp_low': day.get('tempMin', ''),
                        'desc': day.get('textDay', ''),
                        'icon': _text_to_icon(day.get('textDay', '')),
                    }
                    for day in fc_data.get('daily', [])
                ]

        return {
            'success': True,
            'city': city,
            'current': {
                'temp': now.get('temp', 'N/A'),
                'humidity': now.get('humidity', 'N/A'),
                'wind': now.get('windSpeed', 'N/A'),
                'desc': now.get('text', ''),
                'icon': _text_to_icon(now.get('text', '')),
            },
            'forecast': fc_days or _mock_forecast(),
        }
    except Exception as e:
        print(f"和风天气获取失败: {e}")
    return None


def _fetch_weather_china(city: str) -> Optional[Dict]:
    """中国天气网 API（无需 Key）"""
    try:
        code = CITY_CODE_MAP.get(city, '101020100')
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'http://www.weather.com.cn/',
        }
        # 实时天气
        sk_url = f'http://www.weather.com.cn/data/sk/{code}.html'
        sk_resp = requests.get(sk_url, timeout=10, headers=headers)
        if sk_resp.status_code != 200:
            return None
        sk_data = sk_resp.json().get('weatherinfo', {})
        temp = sk_data.get('temp', 'N/A')
        humidity = sk_data.get('humidity', 'N/A').replace('%', '')
        wind = sk_data.get('WD', '') + sk_data.get('WS', '')

        # 天气描述
        desc = ''
        try:
            ci_url = f'http://www.weather.com.cn/data/cityinfo/{code}.html'
            ci_resp = requests.get(ci_url, timeout=5, headers=headers)
            if ci_resp.status_code == 200:
                desc = ci_resp.json().get('weatherinfo', {}).get('weather', '')
        except:
            pass

        return {
            'success': True,
            'city': city,
            'current': {
                'temp': temp,
                'humidity': humidity,
                'wind': wind,
                'desc': desc,
                'icon': _text_to_icon(desc),
            },
            'forecast': _fetch_qforecast(code) or _mock_forecast(),
        }
    except Exception as e:
        print(f"中国天气网获取失败: {e}")
    return None


def _fetch_qforecast(location_code: str) -> Optional[List[Dict]]:
    """尝试用和风天气获取预报（如果配置了 Key）"""
    api_key = os.environ.get('QWEATHER_API_KEY', '')
    if not api_key:
        return None
    try:
        loc = location_code[-9:] if len(location_code) > 9 else location_code[-6:]
        url = f'https://devapi.qweather.com/v7/weather/3d?location={loc}&key={api_key}'
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('code') == '200':
                return [
                    {
                        'date': day.get('fxDate', ''),
                        'temp_high': day.get('tempMax', ''),
                        'temp_low': day.get('tempMin', ''),
                        'desc': day.get('textDay', ''),
                        'icon': _text_to_icon(day.get('textDay', '')),
                    }
                    for day in data.get('daily', [])
                ]
    except:
        pass
    return None


def _fetch_weather_wttr(city: str) -> Optional[Dict]:
    """wttr.in 备用（国外服务器友好）"""
    try:
        url = f"https://wttr.in/{quote(city)}?format=j1&lang=zh"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            current = data.get('current_condition', [{}])[0]
            forecast = data.get('weather', [])[:5]
            return {
                'success': True,
                'city': city,
                'current': {
                    'temp': current.get('temp_C', 'N/A'),
                    'humidity': current.get('humidity', 'N/A'),
                    'wind': current.get('windspeedKmph', 'N/A'),
                    'desc': current.get('lang_zh', [{}])[0].get('value', '') if current.get('lang_zh') else '',
                    'icon': current.get('weatherCode', ''),
                },
                'forecast': [
                    {
                        'date': day.get('date', ''),
                        'temp_high': day.get('maxtempC', ''),
                        'temp_low': day.get('mintempC', ''),
                        'desc': day.get('hourly', [{}])[0].get('lang_zh', [{}])[0].get('value', ''),
                        'icon': day.get('hourly', [{}])[0].get('weatherCode', ''),
                    }
                    for day in forecast
                ]
            }
    except Exception as e:
        print(f"wttr.in 获取失败: {e}")
    return None


def _text_to_icon(text: str) -> str:
    """天气文字转图标编码"""
    if '晴' in text:
        return '113'
    if '多云' in text or '少云' in text:
        return '116'
    if '阴' in text:
        return '119'
    if '雨' in text:
        return '296'
    if '雪' in text:
        return '338'
    if '雾' in text or '霾' in text:
        return '143'
    if '雷' in text:
        return '200'
    return '113'


def _mock_forecast() -> List[Dict]:
    """模拟天气预报"""
    today = date.today()
    conditions = ["晴", "多云", "阴", "小雨", "晴转多云"]
    icons = ["113", "116", "119", "296", "116"]
    return [
        {
            'date': (today + timedelta(days=i)).isoformat(),
            'temp_high': str(random.randint(22, 35)),
            'temp_low': str(random.randint(15, 24)),
            'desc': random.choice(conditions),
            'icon': random.choice(icons),
        }
        for i in range(5)
    ]


def _mock_weather(city: str) -> Dict:
    """模拟天气数据"""
    today = date.today()
    conditions = ["晴", "多云", "阴", "小雨", "晴转多云"]
    icons = ["113", "116", "119", "296", "116"]
    idx = random.randint(0, 4)
    return {
        'success': True,
        'city': city,
        'current': {
            'temp': str(random.randint(18, 32)),
            'humidity': str(random.randint(40, 80)),
            'wind': str(random.randint(5, 25)),
            'desc': conditions[idx],
            'icon': icons[idx],
        },
        'forecast': _mock_forecast(),
    }


# ===== RSS 新闻抓取（国内可访问源）=====

RSS_FEEDS = {
    'ai': [
        'https://www.36kr.com/feed',                  # 36氪
        'https://feed.infoq.cn/',                     # InfoQ
    ],
    'internet': [
        'https://www.huxiu.com/rss/0.xml',            # 虎嗅
        'https://feed.appinn.com/',                   # 小众软件
    ],
    'investment': [
        'https://finance.sina.com.cn/rss/gncj.xml',   # 新浪财经国内
        'https://finance.sina.com.cn/rss/gjcj.xml',   # 新浪财经国际
        'https://feedx.net/rss/36kr.xml',              # 36氪(备)
    ],
}


def _parse_rss_feed(url: str, max_items: int = 10) -> List[Dict]:
    """从 RSS feed 获取新闻"""
    try:
        resp = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        if resp.status_code != 200:
            return []
        content = resp.content

        items = []
        # 标准 RSS 2.0
        for entry in re.findall(r'<item>(.*?)</item>', content.decode('utf-8', errors='ignore'), re.DOTALL):
            if len(items) >= max_items:
                break
            title = re.search(r'<title>(.*?)</title>', entry)
            link = re.search(r'<link>(.*?)</link>', entry)
            desc = re.search(r'<description>(.*?)</description>', entry, re.DOTALL)
            pub_date = re.search(r'<pubDate>(.*?)</pubDate>', entry)
            items.append({
                'title': title.group(1) if title else '',
                'url': link.group(1) if link else '#',
                'summary': re.sub(r'<[^>]+>', '', desc.group(1))[:200] if desc else '',
                'time': pub_date.group(1) if pub_date else '',
            })

        # Atom 格式
        if not items:
            for entry in re.findall(r'<entry>(.*?)</entry>', content.decode('utf-8', errors='ignore'), re.DOTALL):
                if len(items) >= max_items:
                    break
                title = re.search(r'<title[^>]*>(.*?)</title>', entry)
                link_m = re.search(r'<link[^>]*href="(.*?)"', entry)
                summary = re.search(r'<summary[^>]*>(.*?)</summary>', entry, re.DOTALL)
                updated = re.search(r'<updated>(.*?)</updated>', entry)
                items.append({
                    'title': title.group(1) if title else '',
                    'url': link_m.group(1) if link_m else '#',
                    'summary': re.sub(r'<[^>]+>', '', summary.group(1))[:200] if summary else '',
                    'time': updated.group(1) if updated else '',
                })

        return items
    except Exception as e:
        print(f"RSS 获取失败 ({url}): {e}")
        return []


def fetch_news(category: str = 'ai', max_items: int = 12) -> List[Dict]:
    """按分类获取新闻"""
    all_items = []
    for feed_url in RSS_FEEDS.get(category, []):
        items = _parse_rss_feed(feed_url, max_items)
        all_items.extend(items)
        if len(all_items) >= max_items:
            break

    if all_items:
        return all_items[:max_items]

    return _mock_news(category, max_items)


def _mock_news(category: str, count: int) -> List[Dict]:
    """模拟新闻数据"""
    now = datetime.now()
    mock_data = {
        'ai': [
            {'title': 'OpenAI 发布 GPT-5，推理能力大幅提升', 'summary': 'OpenAI 今日发布了下一代大语言模型 GPT-5，在数学推理、代码生成和多模态理解方面取得重大突破。', 'source': '36氪'},
            {'title': '国内大模型厂商竞相降价，AI 应用成本下降 80%', 'summary': '字节跳动、百度、阿里等国内大模型厂商纷纷下调 API 调用价格。', 'source': '36氪'},
            {'title': 'AI 编程助手 GitHub Copilot 市场份额突破 40%', 'summary': '据最新报告显示，GitHub Copilot 在全球 AI 编程助手市场份额已超过 40%。', 'source': 'InfoQ'},
            {'title': '斯坦福发布 AI 指数报告：AI 投资创历史新高', 'summary': '斯坦福大学发布的 2025 AI 指数报告显示，全球 AI 投资总额已超过 2000 亿美元。', 'source': '机器之心'},
            {'title': '中国 AI 论文数量和质量均居世界前列', 'summary': 'Nature 指数显示，中国在 AI 领域的论文发表数量和被引用次数均位居全球第一。', 'source': '科技日报'},
        ],
        'internet': [
            {'title': '抖音电商 2025 年 GMV 突破 3 万亿', 'summary': '抖音电商公布 2025 年业绩，全年 GMV 突破 3 万亿元人民币。', 'source': '晚点财经'},
            {'title': '苹果 Vision Pro 2 发布，重量减轻 30%', 'summary': '苹果今日发布第二代混合现实头显 Vision Pro 2，重量减轻 30%。', 'source': '虎嗅'},
            {'title': '小米汽车 SU7 年度交付量超 15 万台', 'summary': '小米汽车宣布 SU7 上市一年累计交付突破 15 万台。', 'source': '新浪科技'},
            {'title': '微信小程序日活用户突破 6 亿', 'summary': '微信公开课数据显示，小程序日活跃用户已突破 6 亿。', 'source': '腾讯科技'},
            {'title': '华为鸿蒙生态设备数超 10 亿', 'summary': '华为宣布搭载鸿蒙操作系统的设备数量已超过 10 亿。', 'source': '华为官方'},
        ],
        'investment': [
            {'title': 'A 股三大指数全线上涨', 'summary': '今日 A 股三大指数全线走高，两市成交额突破 1.5 万亿。', 'source': '东方财富'},
            {'title': '美联储维持利率不变，美元指数走弱', 'summary': '美联储在最新议息会议上宣布维持基准利率不变。', 'source': '华尔街见闻'},
            {'title': '北向资金今日净买入超百亿', 'summary': '北向资金今日大幅净买入 128 亿元，创近三个月新高。', 'source': '证券时报'},
            {'title': '新能源板块集体爆发', 'summary': '受政策利好推动，新能源板块今日全面爆发。', 'source': '中国基金报'},
            {'title': '比特币突破 10 万美元', 'summary': '比特币价格突破 10 万美元大关，加密市场总市值创历史新高。', 'source': 'CoinDesk'},
        ],
    }
    items = mock_data.get(category, [])
    return [
        {
            'title': item['title'],
            'url': '#',
            'summary': item['summary'],
            'source': item['source'],
            'time': (now - timedelta(hours=i * 3)).isoformat(),
        }
        for i, item in enumerate(items)
    ][:count]


# ===== 八点一刻（每日简报）=====

def fetch_daily_briefing() -> Dict:
    """生成每日简报（八点一刻）"""
    today = date.today()
    weekday_cn = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][today.weekday()]

    news_headers = fetch_news('ai', 3)
    investment = fetch_news('investment', 3)

    return {
        'date': today.isoformat(),
        'weekday': weekday_cn,
        'greeting': f'早上好！今天是 {today.month}月{today.day}日 {weekday_cn}',
        'weather_summary': '今日天气晴好，适合外出活动。',
        'headlines': [
            {'title': item['title'], 'source': item.get('source', '')}
            for item in news_headers[:3]
        ],
        'market_snapshots': [
            {'title': item['title'], 'source': item.get('source', '')}
            for item in investment[:3]
        ],
        'inspiration': {
            'quote': '千里之行，始于足下。',
            'author': '老子',
        },
        'recommendation': '今天推荐阅读 AI 行业的最新发展动态。',
    }


# ===== 节假日（API + 本地缓存）=====

def _fetch_holidays_from_api() -> Optional[List[Dict]]:
    """从 timor.tech 获取节假日（免费，无需 Key）"""
    try:
        year = date.today().year
        url = f'https://timor.tech/api/holiday/year/{year}'
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('code') == 0:
                holidays = []
                for date_str, info in data.get('holiday', {}).items():
                    if info.get('holiday'):
                        holidays.append({
                            'name': info['name'],
                            'date': date_str,
                            'days': info.get('wage') or 1,
                        })
                return holidays
    except Exception as e:
        print(f"节假日 API 获取失败: {e}")
    return None


# 本地兜底数据
LOCAL_HOLIDAYS_2026 = [
    {'name': '元旦', 'date': '2026-01-01', 'days': 3, 'type': '法定假日'},
    {'name': '春节', 'date': '2026-02-17', 'days': 7, 'type': '法定假日'},
    {'name': '清明节', 'date': '2026-04-04', 'days': 3, 'type': '法定假日'},
    {'name': '劳动节', 'date': '2026-05-01', 'days': 5, 'type': '法定假日'},
    {'name': '端午节', 'date': '2026-06-19', 'days': 3, 'type': '法定假日'},
    {'name': '中秋节', 'date': '2026-09-25', 'days': 3, 'type': '法定假日'},
    {'name': '国庆节', 'date': '2026-10-01', 'days': 7, 'type': '法定假日'},
]


def fetch_upcoming_holidays(max_count: int = 5) -> List[Dict]:
    """获取最近的节假日"""
    today = date.today()

    # 尝试 API
    api_holidays = _fetch_holidays_from_api()
    local_holidays = LOCAL_HOLIDAYS_2026

    # 合并：API 优先
    source = api_holidays or local_holidays

    upcoming = []
    for h in source:
        h_date = date.fromisoformat(h['date'])
        if h_date >= today:
            upcoming.append({
                'name': h['name'],
                'date': h['date'],
                'days_until': (h_date - today).days,
                'duration': h.get('days', 3),
                'type': h.get('type', '法定假日'),
            })

    return upcoming[:max_count]


# ===== 总体工作台数据 =====

def get_workbench_data(city: str = "昆明") -> Dict:
    """获取工作台所有数据"""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    results = {}

    def fetch_all():
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                'weather': executor.submit(fetch_weather, city),
                'news_ai': executor.submit(fetch_news, 'ai'),
                'news_internet': executor.submit(fetch_news, 'internet'),
                'news_investment': executor.submit(fetch_news, 'investment'),
                'briefing': executor.submit(fetch_daily_briefing),
                'holidays': executor.submit(fetch_upcoming_holidays),
            }
            for key, future in futures.items():
                try:
                    results[key] = future.result()
                except Exception as e:
                    print(f"{key} 获取失败: {e}")
                    results[key] = None

    fetch_all()
    return results
