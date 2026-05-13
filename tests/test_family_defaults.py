"""
测试新家庭默认数据初始化功能
"""
import sys
sys.path.insert(0, 'e:/myAgent')

from family_agent.database import DatabaseManager
from family_agent.family_auth import FamilyAuth
import os
from dotenv import load_dotenv

load_dotenv()

def test_family_defaults():
    """测试创建家庭时的默认数据初始化"""
    
    print("=" * 60)
    print("测试：新家庭默认数据初始化")
    print("=" * 60)
    
    try:
        # 初始化数据库
        db = DatabaseManager()
        auth = FamilyAuth(db)
        
        # 创建测试家庭
        print("\n1️⃣  创建测试家庭...")
        result = auth.create_family("测试家庭", "张三")
        
        if not result.get('family_id'):
            print(f"❌ 创建失败: {result}")
            return
        
        family_id = result['family_id']
        print(f"✅ 家庭创建成功!")
        print(f"   家庭号: {family_id}")
        print(f"   消息: {result['message']}")
        
        # 检查默认成员
        print("\n2️⃣  检查默认家庭成员...")
        members = db.get_all_members()
        print(f"   成员数量: {len(members)}")
        for member in members:
            print(f"   - {member['name']} (角色: {member['role']}, 年龄: {member['age']})")
        
        # 检查购物清单
        print("\n3️⃣  检查初始购物清单...")
        shopping = db.get_shopping_list()
        print(f"   商品数量: {len(shopping)}")
        for item in shopping:
            print(f"   - {item['name']} ({item['quantity']}) [{item['category']}]")
        
        # 检查日程安排
        print("\n4️⃣  检查示例日程安排...")
        from datetime import date
        today = date.today().isoformat()
        reminders = db.get_reminders_by_date(today)
        print(f"   今日日程: {len(reminders)} 条")
        for reminder in reminders:
            print(f"   - {reminder['event']}")
        
        # 检查通知
        print("\n5️⃣  检查欢迎通知...")
        notifications = db.get_notifications(limit=10)
        print(f"   通知数量: {len(notifications)}")
        for notif in notifications[:3]:  # 只显示前3条
            print(f"   - [{notif['type']}] {notif['title']}")
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！默认数据已成功初始化")
        print("=" * 60)
        
        # 清理测试数据（可选）
        cleanup = input("\n是否删除测试家庭？(y/n): ")
        if cleanup.lower() == 'y':
            db.remove_family(family_id)
            print("测试数据已清理")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_family_defaults()
