import pytest
from family_agent.llm_adapter import LLMAdapter
from family_agent.smart_photo_analyzer import SmartPhotoAnalyzer
from family_agent.photo_memory import PhotoMemoryManager


def test_llm_adapter_has_analyze_image_method():
    """Test that LLMAdapter has analyze_image method"""
    adapter = LLMAdapter(provider="mock")
    assert hasattr(adapter, 'analyze_image'), "LLMAdapter missing analyze_image method"
    assert callable(getattr(adapter, 'analyze_image')), "analyze_image is not callable"


def test_analyze_image_returns_dict():
    """Test analyze_image returns a dict"""
    adapter = LLMAdapter(provider="mock")
    result = adapter.analyze_image("test.jpg", "Describe this image")
    assert isinstance(result, dict), "Should return dict"
    assert "description" in result
    assert "tags" in result
    assert "people" in result
    assert "mood" in result


def test_smart_photo_analyzer_can_analyze():
    """Test SmartPhotoAnalyzer can analyze photo without AttributeError"""
    adapter = LLMAdapter(provider="mock")
    photo_manager = PhotoMemoryManager(photo_dir="photos", index_file="data/photo_index.json")
    analyzer = SmartPhotoAnalyzer(photo_manager=photo_manager, llm_adapter=adapter)
    # Should not raise AttributeError
    result = analyzer._analyze_single_photo(type('Photo', (), {'filename': 'test.jpg', 'photo_id': 'test123'})())
    assert isinstance(result, dict) or result is None
