from family_agent.memory_manager import FamilyMemoryManager, MemoryType
from pathlib import Path


def _memory_manager(tmp_path: Path) -> FamilyMemoryManager:
    manager = FamilyMemoryManager.__new__(FamilyMemoryManager)
    manager.data_dir = tmp_path
    manager.short_term_memory = []
    manager.max_short_term = 50
    manager.compress_after = 36
    manager.keep_recent_after_compress = 18
    manager.conversation_summaries = []
    manager.working_memory = {}
    manager.chroma_client = None
    manager.long_term_collection = None
    manager.long_term_fallback = []
    manager.chroma_path = Path("memory-test")
    return manager


def test_extracts_and_classifies_durable_facts(tmp_path):
    manager = _memory_manager(tmp_path)

    promoted = manager.remember_conversation_turn(
        "我喜欢喝乌龙茶，妈妈对花生过敏",
        user_id="me",
    )

    assert promoted
    context = manager.build_chat_context("妈妈能吃花生吗", user_id="me")
    assert "花生" in context
    assert manager.classify_fact("妈妈对花生过敏") == "health"
    assert manager.extract_memorable_facts("我喜欢喝乌龙茶，妈妈对花生过敏") == [
        "我喜欢喝乌龙茶",
        "妈妈对花生过敏",
    ]


def test_chat_context_filters_user_specific_memories(tmp_path):
    manager = _memory_manager(tmp_path)

    manager.remember_conversation_turn("我喜欢喝乌龙茶", user_id="alice")
    manager.remember_conversation_turn("我喜欢喝咖啡", user_id="bob")

    alice_context = manager.build_chat_context("喜欢喝什么", user_id="alice")
    bob_context = manager.build_chat_context("喜欢喝什么", user_id="bob")

    assert "乌龙茶" in alice_context
    assert "咖啡" not in alice_context
    assert "咖啡" in bob_context
    assert "乌龙茶" not in bob_context


def test_short_term_memory_compresses_to_summary(tmp_path):
    manager = _memory_manager(tmp_path)
    manager.compress_after = 6
    manager.keep_recent_after_compress = 3

    for index in range(8):
        manager.remember_conversation_turn(
            f"第{index}轮 我喜欢喝茶，请提醒我买牛奶",
            assistant_response="好的，我记下了",
            user_id="me",
        )

    stats = manager.get_memory_stats()
    assert stats["summary_count"] >= 1
    assert stats["short_term_count"] <= manager.compress_after

    context = manager.build_chat_context("买牛奶", user_id="me", max_chars=1200)
    assert "压缩会话摘要" in context
    assert "买牛奶" in context


def test_context_respects_budget(tmp_path):
    manager = _memory_manager(tmp_path)
    for index in range(20):
        manager.add_memory(
            content="很长的上下文" * 20,
            memory_type=MemoryType.SHORT_TERM,
        )

    context = manager.build_chat_context("上下文", max_chars=300)
    assert len(context) <= 320
