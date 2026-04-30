"""
数据库测试
"""
import pytest
import os
from family_agent.database import DatabaseManager


@pytest.fixture
def db():
    """创建测试数据库"""
    test_db = DatabaseManager("data/test_family_agent.db")
    yield test_db
    # 清理测试数据库
    test_db.close()
    if os.path.exists("data/test_family_agent.db"):
        os.remove("data/test_family_agent.db")


def test_add_member(db):
    """测试添加成员"""
    result = db.add_member("测试用户", "父亲", 40)
    assert result is True
    
    members = db.get_all_members()
    assert len(members) == 1
    assert members[0]['name'] == "测试用户"


def test_duplicate_member(db):
    """测试重复成员"""
    db.add_member("测试用户", "父亲", 40)
    result = db.add_member("测试用户", "母亲", 35)
    assert result is False


def test_remove_member(db):
    """测试删除成员"""
    db.add_member("测试用户", "父亲", 40)
    result = db.remove_member("测试用户")
    assert result is True
    
    members = db.get_all_members()
    assert len(members) == 0


def test_shopping_item(db):
    """测试购物项"""
    db.add_shopping_item("牛奶", "2", "食品", "high", "张三")
    
    items = db.get_all_shopping_items()
    assert len(items) == 1
    assert items[0]['name'] == "牛奶"
    
    db.remove_shopping_item("牛奶")
    items = db.get_all_shopping_items()
    assert len(items) == 0


def test_reminder(db):
    """测试日程"""
    db.add_reminder("2026-05-01", "劳动节")
    
    reminders = db.get_all_reminders()
    assert len(reminders) == 1
    assert reminders[0]['event'] == "劳动节"


def test_chat_history(db):
    """测试聊天历史"""
    db.add_chat_message("user1", "user", "你好")
    db.add_chat_message("user1", "assistant", "你好!有什么我可以帮你的?")
    
    history = db.get_chat_history("user1")
    assert len(history) == 2
    assert history[0]['role'] == "user"
    assert history[1]['role'] == "assistant"


def test_task_management(db):
    """测试任务管理"""
    db.add_task("task_001", "张三", "李四", "买牛奶")
    
    tasks = db.get_my_tasks("李四")
    assert len(tasks) == 1
    assert tasks[0]['content'] == "买牛奶"
    
    db.complete_task("task_001")
    tasks = db.get_my_tasks("李四", status='pending')
    assert len(tasks) == 0


def test_stats(db):
    """测试统计数据"""
    db.add_member("测试用户", "父亲", 40)
    db.add_reminder("2026-05-01", "劳动节")
    db.add_shopping_item("牛奶", "2")
    
    stats = db.get_stats()
    assert stats['members_count'] == 1
    assert stats['reminders_count'] == 1
    assert stats['shopping_items_count'] == 1
