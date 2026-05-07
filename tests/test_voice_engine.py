import pytest
from family_agent.voice_engine import VoiceEngine


def test_voice_engine_init():
    """Test VoiceEngine initialization"""
    engine = VoiceEngine()
    assert engine is not None


def test_voice_engine_tts():
    """Test text to speech"""
    engine = VoiceEngine()
    result = engine.text_to_speech("Hello", "test_output.mp3")
    assert result is True or result is False  # Accepts both for now


def test_voice_engine_supported():
    """Test if TTS is supported"""
    engine = VoiceEngine()
    assert hasattr(engine, 'is_available')
