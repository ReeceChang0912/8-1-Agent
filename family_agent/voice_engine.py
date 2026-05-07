"""
Voice Engine for TTS (Text-to-Speech)
Supports offline TTS using pyttsx3 or online API
"""
from typing import Optional
import os


class VoiceEngine:
    """Text-to-Speech engine"""

    def __init__(self, use_online: bool = False):
        self.use_online = use_online
        self.online_available = self._check_online_available()
        self.offline_engine = None
        if not use_online:
            self._init_offline_engine()

    def _check_online_available(self) -> bool:
        """Check if online TTS is available"""
        try:
            import requests
            return True
        except:
            return False

    def _init_offline_engine(self):
        """Initialize offline TTS engine"""
        try:
            import pyttsx3
            self.offline_engine = pyttsx3.init()
            self.offline_engine.setProperty('rate', 150)
            self.offline_engine.setProperty('volume', 0.9)
        except ImportError:
            self.offline_engine = None

    def is_available(self) -> bool:
        """Check if TTS is available"""
        if self.use_online:
            return self.online_available
        return self.offline_engine is not None

    def text_to_speech(self, text: str, output_path: Optional[str] = None) -> bool:
        """
        Convert text to speech
        Args:
            text: Text to convert
            output_path: Output file path (optional)
        Returns:
            True if successful
        """
        if self.use_online:
            return self._online_tts(text, output_path)
        else:
            return self._offline_tts(text, output_path)

    def _offline_tts(self, text: str, output_path: Optional[str]) -> bool:
        """Offline TTS using pyttsx3"""
        if not self.offline_engine:
            return False
        try:
            if output_path:
                self.offline_engine.save_to_file(text, output_path)
                self.offline_engine.runAndWait()
            else:
                self.offline_engine.say(text)
                self.offline_engine.runAndWait()
            return True
        except:
            return False

    def _online_tts(self, text: str, output_path: Optional[str]) -> bool:
        """Online TTS using API (placeholder)"""
        # TODO: Implement actual online TTS API call
        return False
