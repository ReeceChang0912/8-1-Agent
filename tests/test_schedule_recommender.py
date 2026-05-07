import pytest
from family_agent.schedule_recommender import SmartScheduleRecommender


def test_schedule_recommender_analyze_patterns():
    """Test historical pattern analysis"""
    recommender = SmartScheduleRecommender(data_dir="data")
    patterns = recommender.analyze_historical_patterns("张三")
    assert isinstance(patterns, dict), "Should return dict"


def test_schedule_recommender_suggest():
    """Test schedule recommendation"""
    recommender = SmartScheduleRecommender(data_dir="data")
    suggestions = recommender.recommend_schedule("张三", "2026-05-10")
    assert isinstance(suggestions, list), "Should return list"


def test_schedule_recommender_free_time():
    """Test free time prediction"""
    recommender = SmartScheduleRecommender(data_dir="data")
    free_times = recommender.predict_free_time("张三", "2026-05-10")
    assert isinstance(free_times, list), "Should return list"
