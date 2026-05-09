"""
数据迁移 + 模拟数据生成
1. 将现有 JSON 数据导入 PostgreSQL
2. 生成一个家庭的完整模拟数据
"""
import sys
import os
# 修复 Windows 控制台 UTF-8 编码问题
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
import secrets

from family_agent.database import DatabaseManager

DATA_DIR = Path(__file__).parent.parent / "data"
db = DatabaseManager()


# ===== 1. 迁移现有 JSON 数据 =====

def migrate_members():
    """迁移成员数据"""
    path = DATA_DIR / "members.json"
    if not path.exists():
        return 0
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # 支持两种格式: 列表 或 字典
    if isinstance(data, dict):
        data = list(data.values())
    count = 0
    for item in data:
        name = item.get('name', item.get('username', ''))
        if not name:
            continue
        try:
            db.add_member(
                name=name,
                role=item.get('role', '成员'),
                age=item.get('age', 30),
                side=item.get('side', 'core'),
                interaction_style=item.get('interaction_style', 'peer'),
                permission=item.get('permission', 'member'),
                preferences=item.get('preferences', [])
            )
            count += 1
        except Exception as e:
            print(f"  跳过成员 {name}: {e}")
    return count


def migrate_shopping():
    """迁移购物清单"""
    path = DATA_DIR / "shopping_list.json"
    if not path.exists():
        return 0
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = data.get('items', list(data.values()))
    count = 0
    for item in data:
        try:
            db.add_shopping_item(
                name=item.get('name', '未知物品'),
                quantity=item.get('quantity', '1'),
                category=item.get('category', 'general'),
                priority=item.get('priority', 'normal'),
                added_by=item.get('added_by', item.get('addedBy', '')),
                status=item.get('status', 'pending') if not item.get('purchased') else 'purchased'
            )
            count += 1
        except Exception as e:
            print(f"  跳过购物项: {e}")
    return count


def migrate_reminders():
    """迁移日程"""
    path = DATA_DIR / "reminders.json"
    if not path.exists():
        return 0
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = list(data.values())
    count = 0
    for item in data:
        try:
            db.add_reminder(
                date=item.get('date', item.get('time', datetime.now().isoformat())[:10]),
                event=item.get('event', item.get('title', '待办事项')),
                member=item.get('member', item.get('assigned_to', ''))
            )
            count += 1
        except Exception as e:
            print(f"  跳过日程: {e}")
    return count


def migrate_chat_history():
    """迁移聊天历史"""
    path = DATA_DIR / "chat_history.json"
    if not path.exists():
        return 0
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    count = 0
    if isinstance(data, dict):
        for user_id, messages in data.items():
            for msg in messages:
                try:
                    db.add_chat_message(
                        user_id=user_id,
                        role=msg.get('role', 'user'),
                        content=msg.get('content', ''),
                        emotion=msg.get('emotion')
                    )
                    count += 1
                except:
                    pass
    return count


def migrate_invites():
    """迁移邀请"""
    path = DATA_DIR / "invites.json"
    if not path.exists():
        return 0
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    count = 0
    for item in data:
        try:
            db.add_invite(
                code=item.get('code', hashlib.md5(str(datetime.now()).encode()).hexdigest()[:12]),
                family_id=item.get('family_id', 'default'),
                creator=item.get('creator', 'system'),
                expires_at=item.get('expires_at', (datetime.now() + timedelta(days=7)).isoformat())
            )
            count += 1
        except:
            pass
    return count


def migrate_data():
    """执行所有数据迁移"""
    print("=" * 50)
    print("📦 迁移现有 JSON 数据到 PostgreSQL")
    print("=" * 50)

    print("\n📋 迁移成员...")
    c = migrate_members()
    print(f"  完成: {c} 条")

    print("\n🛒 迁移购物清单...")
    c = migrate_shopping()
    print(f"  完成: {c} 条")

    print("\n📅 迁移日程...")
    c = migrate_reminders()
    print(f"  完成: {c} 条")

    print("\n💬 迁移聊天历史...")
    c = migrate_chat_history()
    print(f"  完成: {c} 条")

    print("\n📨 迁移邀请...")
    c = migrate_invites()
    print(f"  完成: {c} 条")

    print("\n✅ 数据迁移完成!")


# ===== 2. 生成模拟数据 =====

FAMILY_DATA = {
    'family_id': '888888',
    'family_name': '高家&常家',
    'members': [
        # 高家
        {'name': '高鹏', 'role': '爸爸', 'age': 58, 'side': 'core', 'permission': 'admin', 'interaction_style': 'peer'},
        {'name': '老高', 'role': '爸爸', 'age': 58, 'side': 'core', 'permission': 'admin', 'interaction_style': 'peer'},
        {'name': '孙梦邻', 'role': '妈妈', 'age': 55, 'side': 'core', 'permission': 'admin', 'interaction_style': 'peer'},
        {'name': '老孙', 'role': '妈妈', 'age': 55, 'side': 'core', 'permission': 'admin', 'interaction_style': 'peer'},
        {'name': '高瑜敏', 'role': '女儿', 'age': 32, 'side': 'core', 'permission': 'member', 'interaction_style': 'peer'},
        {'name': '方', 'role': '女儿', 'age': 32, 'side': 'core', 'permission': 'member', 'interaction_style': 'peer'},
        {'name': '高玉米', 'role': '女儿', 'age': 32, 'side': 'core', 'permission': 'member', 'interaction_style': 'peer'},
        {'name': '高Tia', 'role': '女儿', 'age': 32, 'side': 'core', 'permission': 'member', 'interaction_style': 'peer'},
        {'name': '高孙竞瑀', 'role': '儿子', 'age': 28, 'side': 'core', 'permission': 'member', 'interaction_style': 'peer'},
        {'name': '高孙', 'role': '儿子', 'age': 28, 'side': 'core', 'permission': 'member', 'interaction_style': 'peer'},
        {'name': '小宝', 'role': '儿子', 'age': 28, 'side': 'core', 'permission': 'member', 'interaction_style': 'peer'},
        {'name': '子成', 'role': '儿子', 'age': 28, 'side': 'core', 'permission': 'member', 'interaction_style': 'peer'},
        {'name': '竞瑀', 'role': '儿子', 'age': 28, 'side': 'core', 'permission': 'member', 'interaction_style': 'peer'},
        # 常家
        {'name': '常正伟', 'role': '爸爸', 'age': 60, 'side': 'extended', 'permission': 'member', 'interaction_style': 'peer'},
        {'name': '老常', 'role': '爸爸', 'age': 60, 'side': 'extended', 'permission': 'member', 'interaction_style': 'peer'},
        {'name': '王云芬', 'role': '妈妈', 'age': 58, 'side': 'extended', 'permission': 'member', 'interaction_style': 'peer'},
        {'name': '三妹', 'role': '妈妈', 'age': 58, 'side': 'extended', 'permission': 'member', 'interaction_style': 'peer'},
        {'name': '常睿', 'role': '儿子', 'age': 35, 'side': 'core', 'permission': 'admin', 'interaction_style': 'peer'},
    ],
    'shopping_items': [
        {'name': '高钙牛奶', 'quantity': '2箱', 'category': 'food', 'priority': 'high', 'added_by': '高瑜敏'},
        {'name': '土鸡蛋', 'quantity': '30个', 'category': 'food', 'priority': 'high', 'added_by': '高瑜敏'},
        {'name': '进口车厘子', 'quantity': '2斤', 'category': 'food', 'priority': 'normal', 'added_by': '孙梦邻'},
        {'name': '有机面粉', 'quantity': '5kg', 'category': 'food', 'priority': 'normal', 'added_by': '孙梦邻'},
        {'name': '云南鲜花饼', 'quantity': '2盒', 'category': 'food', 'priority': 'normal', 'added_by': '高瑜敏'},
        {'name': '黑人牙膏', 'quantity': '2支', 'category': 'daily', 'priority': 'normal', 'added_by': '常睿'},
        {'name': '竹浆纸巾', 'quantity': '3提', 'category': 'daily', 'priority': 'normal', 'added_by': '常睿'},
        {'name': '蜂花洗发水', 'quantity': '1瓶', 'category': 'daily', 'priority': 'low', 'added_by': '高瑜敏'},
        {'name': '儿童绘本', 'quantity': '5本', 'category': 'other', 'priority': 'low', 'added_by': '高瑜敏'},
        {'name': '感冒灵颗粒', 'quantity': '2盒', 'category': 'health', 'priority': 'high', 'added_by': '孙梦邻'},
    ],
    'reminders': [
        {'date': '2026-05-10', 'event': '老高和老孙结婚纪念日 - 订餐厅', 'member': '常睿'},
        {'date': '2026-05-15', 'event': '给玉米妈妈准备母亲节礼物', 'member': '常睿'},
        {'date': '2026-05-18', 'event': '老常体检复查 - 省人民医院', 'member': '常睿'},
        {'date': '2026-05-20', 'event': '小宝竞瑀面试 - 华为技术岗', 'member': '高鹏'},
        {'date': '2026-05-25', 'event': '全家聚餐 - 老孙掌勺', 'member': '孙梦邻'},
        {'date': '2026-06-01', 'event': '带孩子们去公园野餐', 'member': '高瑜敏'},
        {'date': '2026-06-10', 'event': '三妹王云芬生日 - 订蛋糕', 'member': '常睿'},
        {'date': '2026-06-15', 'event': '老常老两口金婚纪念', 'member': '常睿'},
    ],
    'tasks': [
        {'from': '高瑜敏', 'to': '常睿', 'content': '下班顺路买高钙牛奶和鸡蛋', 'priority': 'high'},
        {'from': '孙梦邻', 'to': '高鹏', 'content': '帮忙预约周六中医馆按摩', 'priority': 'normal'},
        {'from': '常睿', 'to': '高瑜敏', 'content': '帮我整理下季度工作汇报材料', 'priority': 'normal'},
        {'from': '老常', 'to': '常睿', 'content': '帮忙看看新买的智能手机怎么用', 'priority': 'low'},
        {'from': '三妹', 'to': '高瑜敏', 'content': '周末一起逛街买夏装', 'priority': 'normal'},
    ],
    'shopping_history': [
        {'name': '五常大米', 'quantity': '20kg', 'member': '常睿'},
        {'name': '鲁花花生油', 'quantity': '2桶', 'member': '常睿'},
        {'name': '海天生抽', 'quantity': '2瓶', 'member': '高瑜敏'},
        {'name': '手工饺子', 'quantity': '3袋', 'member': '高瑜敏'},
        {'name': '黑猪后腿肉', 'quantity': '5斤', 'member': '常睿'},
        {'name': '伊利安慕希酸奶', 'quantity': '2提', 'member': '常睿'},
        {'name': '海南香蕉', 'quantity': '3串', 'member': '高瑜敏'},
        {'name': '蓝月亮洗衣液', 'quantity': '2瓶', 'member': '常睿'},
    ],
    'chat_messages': [
        ('高鹏', 'user', '今天天气怎么样？适合带老伴出去走走吗？'),
        ('高鹏', 'assistant', '今天天气晴朗，温度20-26度，非常适合户外活动。建议去西湖边散步，或者去植物园赏花。'),
        ('高瑜敏', 'user', '玉米助手，帮我记一下，周末要买鲜花饼和车厘子'),
        ('高瑜敏', 'assistant', '好的，已经帮你记在购物清单里了！周末超市的进口车厘子应该很新鲜，要不要多买点？'),
        ('常睿', 'user', '老婆，晚上咱们吃什么？'),
        ('常睿', 'assistant', '我看冰箱里有后腿肉、车厘子和饺子。建议做糖醋里脊和清炒时蔬，再来个紫菜蛋花汤，营养又美味！'),
        ('孙梦邻', 'user', '下周末全家聚餐，我打算做10个菜，帮我出个菜单'),
        ('孙梦邻', 'assistant', '好的！建议菜单：红烧肉、清蒸鲈鱼、白灼虾、宫保鸡丁、麻婆豆腐、干煸四季豆、蒜蓉西兰花、酸辣汤、水果拼盘、鲜花饼甜点。需要我帮你记到购物清单里吗？'),
        ('老常', 'user', '小睿，这个新的华为手机怎么设置指纹解锁？'),
        ('老常', 'assistant', '打开设置 → 生物识别和密码 → 指纹 → 输入锁屏密码后按照提示录入指纹就可以了。需要我一步步教您吗？'),
        ('三妹', 'user', '六十大寿想请全家吃顿好的，有推荐吗？'),
        ('三妹', 'assistant', '恭喜三妹！建议去西湖边的楼外楼，环境好菜品正宗，或者去凯悦酒店的自助餐，选择多适合全家老少。要帮您提前预订吗？'),
    ],
}


def seed_mock_data():
    """生成模拟家庭数据"""
    print("\n" + "=" * 50)
    print("🎭 生成模拟家庭数据")
    print("=" * 50)

    data = FAMILY_DATA

    # 1. 创建家庭
    print(f"\n🏠 创建家庭: {data['family_name']} ({data['family_id']})")
    try:
        db.add_family(
            family_id=data['family_id'],
            family_name=data['family_name'],
            members=[m['name'] for m in data['members']]
        )
        print("  ✅ 家庭创建成功")
    except Exception as e:
        print(f"  ⚠️ 家庭已存在或创建失败: {e}")

    # 2. 添加成员
    print("\n👨‍👩‍👧‍👦 添加成员...")
    for m in data['members']:
        try:
            db.add_member(**m)
            print(f"  ✅ {m['name']} ({m['role']})")
        except Exception as e:
            print(f"  ⚠️ {m['name']}: {e}")

    # 3. 添加购物清单
    print("\n🛒 添加购物清单...")
    for item in data['shopping_items']:
        db.add_shopping_item(**item)
    print(f"  ✅ {len(data['shopping_items'])} 项")

    # 4. 添加日程
    print("\n📅 添加日程...")
    for r in data['reminders']:
        db.add_reminder(**r)
    print(f"  ✅ {len(data['reminders'])} 条")

    # 5. 添加任务
    print("\n📋 添加任务...")
    for t in data['tasks']:
        raw = f"{t['from']}_{t['to']}_{datetime.now()}"
        task_id = f"task_{hashlib.md5(raw.encode()).hexdigest()[:12]}"
        db.add_task(
            task_id=task_id,
            from_member=t['from'],
            to_member=t['to'],
            content=t['content'],
            priority=t['priority']
        )
    print(f"  ✅ {len(data['tasks'])} 条")

    # 6. 添加购物历史
    print("\n📦 添加购物历史...")
    for h in data['shopping_history']:
        db.add_shopping_history(**h)
    print(f"  ✅ {len(data['shopping_history'])} 条")

    # 7. 添加聊天历史
    print("\n💬 添加聊天记录...")
    for user_id, role, content in data['chat_messages']:
        db.add_chat_message(user_id=user_id, role=role, content=content)
    print(f"  ✅ {len(data['chat_messages'])} 条")

    # 8. 添加通知
    print("\n🔔 添加通知...")
    notifications = [
        ('Ray', '周末计划提醒', '记得周六下午3点参加小宇的家长会', 'reminder', 'high'),
        ('李婉', '购物提醒', '牛奶和鸡蛋快用完了，记得补货', 'shopping', 'normal'),
        ('小宇', '作业提醒', '今晚有数学作业，记得完成', 'task', 'normal'),
        ('Ray', '缴费提醒', '本月物业费即将到期，请及时缴纳', 'billing', 'high'),
        ('李婉', '母亲节提醒', '明天是母亲节，孩子们准备了惊喜礼物哦！', 'festival', 'normal'),
    ]
    for member, title, msg, ntype, priority in notifications:
        db.add_notification(
            member_name=member,
            title=title,
            message=msg,
            notification_type=ntype,
            priority=priority
        )
    print(f"  ✅ {len(notifications)} 条")

    print("\n" + "=" * 50)
    print("✅ 全部完成！")
    print("=" * 50)

    # 显示最终统计
    stats = db.get_stats()
    print(f"\n📊 数据库统计:")
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == '__main__':
    # 先迁移现有数据
    migrate_data()

    # 再生成模拟数据
    seed_mock_data()

    db.close()
