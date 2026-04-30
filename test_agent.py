"""
家庭智能管家测试脚本
"""

from family_agent.core import FamilyAgentCore
from family_agent.role_manager import FamilyMember, InteractionStyle, PermissionLevel


def test_basic_chat():
    """测试基本对话"""
    print("=" * 60)
    print("测试1: 基本对话")
    print("=" * 60)
    
    agent = FamilyAgentCore()
    
    # 测试对话
    response = agent.chat("你好！")
    print(f"用户: 你好！")
    print(f"助手: {response}\n")
    
    response = agent.chat("我今天有点担心孩子的学习")
    print(f"用户: 我今天有点担心孩子的学习")
    print(f"助手: {response}\n")


def test_member_management():
    """测试成员管理"""
    print("=" * 60)
    print("测试2: 成员管理")
    print("=" * 60)
    
    agent = FamilyAgentCore()
    
    # 添加成员
    dad = FamilyMember(
        name="爸爸",
        role="父亲",
        age=45,
        side="core",
        interaction_style=InteractionStyle.PEER,
        permission=PermissionLevel.ADMIN,
        preferences=["喝茶", "看新闻"]
    )
    
    mom = FamilyMember(
        name="妈妈",
        role="母亲",
        age=42,
        side="core",
        interaction_style=InteractionStyle.PEER,
        permission=PermissionLevel.ADMIN,
        preferences=["烘焙", "瑜伽"]
    )
    
    grandma = FamilyMember(
        name="奶奶",
        role="祖母",
        age=70,
        side="husband_side",
        interaction_style=InteractionStyle.ELDER,
        permission=PermissionLevel.MEMBER,
        health_notes=["高血压", "糖尿病"]
    )
    
    child = FamilyMember(
        name="小明",
        role="孩子",
        age=8,
        side="core",
        interaction_style=InteractionStyle.CHILD,
        permission=PermissionLevel.CHILD
    )
    
    agent.add_member(dad)
    agent.add_member(mom)
    agent.add_member(grandma)
    agent.add_member(child)
    
    print(f"已添加 {len(agent.members)} 个家庭成员")
    
    for name, member in agent.members.items():
        print(f"  - {name} ({member.role}, {member.age}岁)")
    
    print()


def test_knowledge_base():
    """测试知识库"""
    print("=" * 60)
    print("测试3: 知识库")
    print("=" * 60)
    
    agent = FamilyAgentCore()
    
    # 添加知识
    doc_id = agent.knowledge_base.add_text(
        text="""
        高血压患者日常护理要点：
        1. 低盐饮食，每日食盐不超过6克
        2. 规律运动，每周至少150分钟中等强度运动
        3. 按时服药，不要随意停药
        4. 定期监测血压
        5. 保持良好心态，避免情绪波动
        """,
        title="高血压护理指南",
        category="health",
        tags=["高血压", "慢性病", "护理"]
    )
    
    print(f"已添加文档: {doc_id}")
    
    # 搜索知识
    results = agent.knowledge_base.search("高血压注意事项", category="health")
    
    print(f"\n搜索结果 ({len(results)} 条):")
    for i, result in enumerate(results, 1):
        print(f"\n结果 {i}:")
        print(result['content'][:200] + "...")
    
    print()


def test_emotion_detection():
    """测试情感识别"""
    print("=" * 60)
    print("测试4: 情感识别")
    print("=" * 60)
    
    agent = FamilyAgentCore()
    
    test_cases = [
        ("今天真开心！", "joy"),
        ("我很生气，受不了了", "anger"),
        ("好难过，想哭", "sadness"),
        ("有点担心明天的考试", "anxiety"),
        ("今天天气不错", "neutral")
    ]
    
    for text, expected in test_cases:
        result = agent.emotion_engine.detect_emotion(text)
        emotion = result['primary_emotion'].value
        confidence = result['confidence']
        
        status = "✓" if emotion == expected else "✗"
        print(f"{status} \"{text}\" -> {emotion} (置信度: {confidence:.2f})")
    
    print()


def test_memory_system():
    """测试记忆系统"""
    print("=" * 60)
    print("测试5: 记忆系统")
    print("=" * 60)
    
    agent = FamilyAgentCore()
    
    # 添加记忆
    from family_agent.memory_manager import MemoryType
    
    agent.memory_manager.add_memory(
        content="爸爸今年冬天血压有点高",
        memory_type=MemoryType.LONG_TERM,
        importance=0.8,
        tags=["健康", "爸爸"],
        related_members=["爸爸"]
    )
    
    agent.memory_manager.add_memory(
        content="小宝对花粉过敏",
        memory_type=MemoryType.LONG_TERM,
        importance=0.9,
        tags=["健康", "孩子"],
        related_members=["小明"]
    )
    
    print("已添加2条长期记忆")
    
    # 检索记忆
    results = agent.memory_manager.retrieve_memories("血压", n_results=2)
    
    print(f"\n检索'血压'相关记忆 ({len(results)} 条):")
    for result in results:
        print(f"  - {result['content']}")
    
    # 获取统计
    stats = agent.memory_manager.get_memory_stats()
    print(f"\n记忆统计:")
    print(f"  短期记忆: {stats['short_term_count']}")
    print(f"  长期记忆: {stats['long_term_count']}")
    
    print()


def test_tools():
    """测试工具系统"""
    print("=" * 60)
    print("测试6: 工具系统")
    print("=" * 60)
    
    agent = FamilyAgentCore()
    
    # 列出工具
    tools = agent.tool_engine.list_tools()
    print(f"可用工具 ({len(tools)} 个):")
    for tool in tools:
        print(f"  - {tool['name']}: {tool['description']}")
    
    # 测试工具执行
    print("\n测试工具执行:")
    
    result = agent.tool_engine.execute_tool(
        "recommend_gift",
        member_name="奶奶",
        occasion="生日",
        budget=500
    )
    print(f"礼物推荐: {result}")
    
    print()


def main():
    """运行所有测试"""
    print("\n🏡 家庭智能管家 - 功能测试\n")
    
    try:
        test_basic_chat()
        test_member_management()
        test_knowledge_base()
        test_emotion_detection()
        test_memory_system()
        test_tools()
        
        print("=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
