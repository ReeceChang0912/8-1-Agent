"""
工作台数据服务
聚合新闻、天气、节假日等信息
"""
import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from urllib.parse import quote

# ===== 天气 =====

def fetch_weather(city: str = "上海") -> Dict:
    """获取天气信息"""
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
                    'icon': current.get('weatherCode', '') or current.get('weatherDesc', [{}])[0].get('value', ''),
                },
                'forecast': [
                    {
                        'date': day.get('date', ''),
                        'temp_high': day.get('maxtempC', ''),
                        'temp_low': day.get('mintempC', ''),
                        'desc': day.get('hourly', [{}])[0].get('lang_zh', [{}])[0].get('value', '') if day.get('hourly') else '',
                        'icon': day.get('hourly', [{}])[0].get('weatherCode', ''),
                    }
                    for day in forecast
                ]
            }
    except Exception as e:
        print(f"天气获取失败: {e}")

    # 模拟数据
    return _mock_weather(city)


def _mock_weather(city: str) -> Dict:
    """模拟天气数据"""
    today = date.today()
    conditions = ["晴", "多云", "阴", "小雨", "晴转多云"]
    icons = ["113", "116", "119", "296", "116"]
    import random
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
        'forecast': [
            {
                'date': (today + timedelta(days=i)).isoformat(),
                'temp_high': str(random.randint(22, 35)),
                'temp_low': str(random.randint(15, 24)),
                'desc': random.choice(conditions),
                'icon': random.choice(icons),
            }
            for i in range(5)
        ]
    }


# ===== RSS 新闻抓取 =====

RSS_FEEDS = {
    'ai': [
        'https://rsshub.app/36kr/motif/ai',
        'https://rsshub.app/hackernews',
    ],
    'internet': [
        'https://rsshub.app/36kr/news',
        'https://rsshub.app/huxiu/article',
    ],
    'investment': [
        'https://rsshub.app/eastmoney/search/股市',
        'https://rsshub.app/xueqiu/hots',
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

        root = ET.fromstring(resp.content)
        items = []
        # 处理标准 RSS 2.0
        for entry in root.iter('item'):
            if len(items) >= max_items:
                break
            title = entry.findtext('title', '')
            link = entry.findtext('link', '')
            desc = entry.findtext('description', '')
            pub_date = entry.findtext('pubDate', '')
            # 清理 HTML 标签
            import re
            desc = re.sub(r'<[^>]+>', '', desc) if desc else ''
            items.append({
                'title': title,
                'url': link,
                'summary': desc[:200],
                'time': pub_date,
            })

        # 处理 Atom 格式
        if not items:
            for entry in root.iter('{http://www.w3.org/2005/Atom}entry'):
                if len(items) >= max_items:
                    break
                title = entry.findtext('{http://www.w3.org/2005/Atom}title', '')
                link_el = entry.find('{http://www.w3.org/2005/Atom}link')
                link = link_el.get('href', '') if link_el is not None else ''
                summary = entry.findtext('{http://www.w3.org/2005/Atom}summary', '')
                updated = entry.findtext('{http://www.w3.org/2005/Atom}updated', '')
                import re
                summary = re.sub(r'<[^>]+>', '', summary) if summary else ''
                items.append({
                    'title': title,
                    'url': link,
                    'summary': summary[:200],
                    'time': updated,
                })

        return items
    except Exception as e:
        print(f"RSS 获取失败 ({url}): {e}")
        return []


# ===== 新闻聚合 =====

def fetch_news(category: str = 'ai', max_items: int = 12) -> List[Dict]:
    """按分类获取新闻"""
    # 先尝试 RSS
    all_items = []
    for feed_url in RSS_FEEDS.get(category, []):
        items = _parse_rss_feed(feed_url, max_items)
        all_items.extend(items)
        if len(all_items) >= max_items:
            break

    if all_items:
        return all_items[:max_items]

    # 降级到模拟数据
    return _mock_news(category, max_items)


def _mock_news(category: str, count: int) -> List[Dict]:
    """模拟新闻数据"""
    now = datetime.now()
    mock_data = {
        'ai': [
            {'title': 'OpenAI 发布 GPT-5，推理能力大幅提升', 'summary': 'OpenAI 今日发布了下一代大语言模型 GPT-5，在数学推理、代码生成和多模态理解方面取得重大突破。', 'source': '36氪'},
            {'title': 'Google Gemini 2.0 全面开放，支持实时多模态交互', 'summary': 'Google 宣布 Gemini 2.0 面向所有用户开放，新增实时视频理解和语音交互功能。', 'source': 'TechCrunch'},
            {'title': '国内大模型厂商竞相降价，AI 应用成本下降 80%', 'summary': '字节跳动、百度、阿里等国内大模型厂商纷纷下调 API 调用价格，部分模型降价幅度高达 80%。', 'source': '36氪'},
            {'title': 'AI 编程助手 GitHub Copilot 市场份额突破 40%', 'summary': '据最新报告显示，GitHub Copilot 在全球 AI 编程助手市场份额已超过 40%，领先第二名两倍以上。', 'source': 'InfoQ'},
            {'title': '斯坦福发布 AI 指数报告：AI 投资创历史新高', 'summary': '斯坦福大学发布的 2025 AI 指数报告显示，全球 AI 投资总额已超过 2000 亿美元。', 'source': '机器之心'},
            {'title': '中国 AI 论文数量和质量均居世界前列', 'summary': 'Nature 指数显示，中国在 AI 领域的论文发表数量和被引用次数均位居全球第一。', 'source': '科技日报'},
        ],
        'internet': [
            {'title': '抖音电商 2025 年 GMV 突破 3 万亿', 'summary': '抖音电商公布 2025 年业绩，全年 GMV 突破 3 万亿元人民币，同比增长 45%。', 'source': '晚点财经'},
            {'title': '苹果 Vision Pro 2 发布，重量减轻 30%', 'summary': '苹果今日发布第二代混合现实头显 Vision Pro 2，重量减轻 30%，售价降低至 24999 元起。', 'source': '虎嗅'},
            {'title': '小米汽车 SU7 年度交付量超 15 万台', 'summary': '小米汽车宣布 SU7 上市一年累计交付突破 15 万台，超额完成年度目标。', 'source': '新浪科技'},
            {'title': '微信小程序日活用户突破 6 亿', 'summary': '微信公开课数据显示，小程序日活跃用户已突破 6 亿，年交易额同比增长 30%。', 'source': '腾讯科技'},
            {'title': '拼多多 Temu 全球下载量突破 10 亿', 'summary': '拼多多旗下跨境电商平台 Temu 全球累计下载量突破 10 亿次，成为增长最快的电商应用。', 'source': '36氪'},
            {'title': '华为鸿蒙生态设备数超 10 亿', 'summary': '华为宣布搭载鸿蒙操作系统的设备数量已超过 10 亿，成为全球第三大移动操作系统。', 'source': '华为官方'},
        ],
        'investment': [
            {'title': 'A 股三大指数全线上涨，沪指收复 3500 点', 'summary': '今日 A 股三大指数全线走高，上证指数收复 3500 点，两市成交额突破 1.5 万亿。', 'source': '东方财富'},
            {'title': '美联储维持利率不变，美元指数走弱', 'summary': '美联储在最新议息会议上宣布维持基准利率不变，市场预期年内或将降息两次。', 'source': '华尔街见闻'},
            {'title': '北向资金今日净买入超百亿', 'summary': '北向资金今日大幅净买入 128 亿元，创近三个月新高，外资持续看好 A 股市场。', 'source': '证券时报'},
            {'title': '新能源板块集体爆发，光伏ETF涨超 5%', 'summary': '受政策利好推动，新能源板块今日全面爆发，光伏 ETF 涨幅超过 5%，多只个股涨停。', 'source': '中国基金报'},
            {'title': '比特币突破 10 万美元，加密市场总市值创新高', 'summary': '比特币价格突破 10 万美元大关，加密货币总市值达到 3.5 万亿美元，创历史新高。', 'source': 'CoinDesk'},
        ],
    }

    items = mock_data.get(category, [])
    result = []
    for i, item in enumerate(items):
        result.append({
            'title': item['title'],
            'url': '#',
            'summary': item['summary'],
            'source': item['source'],
            'time': (now - timedelta(hours=i * 3)).isoformat(),
        })
    return result[:count]


# ===== 八点一刻（每日简报）=====

def fetch_daily_briefing() -> Dict:
    """生成每日简报（八点一刻）"""
    today = date.today()
    weekday_cn = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][today.weekday()]

    news_headers = fetch_news('ai', 3)
    investment = fetch_news('investment', 3)

    brief = {
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
        'recommendation': '今天推荐阅读 AI 行业的最新发展动态，关注大模型应用落地。',
    }
    return brief


# ===== 节假日 =====

# 2026年中国法定节假日
HOLIDAYS_2026 = [
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
    upcoming = []

    for h in HOLIDAYS_2026:
        h_date = date.fromisoformat(h['date'])
        if h_date >= today:
            days_until = (h_date - today).days
            upcoming.append({
                'name': h['name'],
                'date': h['date'],
                'days_until': days_until,
                'duration': h['days'],
                'type': h.get('type', ''),
            })

    return upcoming[:max_count]


# ===== 总体工作台数据 =====

def get_workbench_data(city: str = "上海") -> Dict:
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
