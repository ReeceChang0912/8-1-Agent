import pytest
from family_agent.smart_shopping import SmartShoppingAdvisor

def test_smart_shopping_analyze_patterns():
    """Test consumption pattern analysis"""
    advisor = SmartShoppingAdvisor(data_dir="data")
    patterns = advisor.analyze_consumption_patterns()
    assert isinstance(patterns, dict), "Should return dict"

def test_smart_shopping_predict_reorder():
    """Test reorder prediction"""
    advisor = SmartShoppingAdvisor(data_dir="data")
    items = advisor.predict_reorder_items()
    assert isinstance(items, list), "Should return list"

def test_smart_shopping_generate_suggestions():
    """Test shopping suggestions for a member"""
    advisor = SmartShoppingAdvisor(data_dir="data")
    suggestions = advisor.generate_shopping_suggestions("张三")
    assert isinstance(suggestions, list), "Should return list"

def test_smart_shopping_record_purchase():
    """Test recording a purchase"""
    advisor = SmartShoppingAdvisor(data_dir="data")
    advisor.record_purchase("测试商品", "1", "测试用户")
    assert len(advisor.history) > 0, "History should have records"
