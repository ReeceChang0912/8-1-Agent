"""
Smart Schedule Recommender - PostgreSQL版
Analyzes historical behavior and recommends schedule
"""
from typing import List, Dict
from datetime import datetime, timedelta
from pathlib import Path
import json


class SmartScheduleRecommender:
    """Recommend schedule based on historical patterns - PostgreSQL版"""

    def __init__(self, db_manager=None, data_dir: str = "data"):
        """
        初始化日程推荐器
        Args:
            db_manager: DatabaseManager 实例
            data_dir: 数据目录（兼容旧接口）
        """
        self.db = db_manager
        self.data_dir = Path(data_dir)

    def analyze_historical_patterns(self, member: str) -> Dict:
        """Analyze historical schedule patterns for a member"""
        if not self.db:
            return {
                'preferred_times': {},
                'preferred_days': {},
                'common_categories': {},
                'avg_duration': 0
            }

        reminders = self.db.get_all_reminders(member=member)

        patterns = {
            'preferred_times': {},  # hour -> count
            'preferred_days': {},   # weekday -> count
            'common_categories': {},
            'avg_duration': 0
        }

        for reminder in reminders:
            # Analyze time preferences
            time_str = reminder.get('time', '09:00')
            try:
                hour = int(time_str.split(':')[0])
                patterns['preferred_times'][hour] = patterns['preferred_times'].get(hour, 0) + 1
            except (ValueError, IndexError):
                pass

            # Analyze day preferences
            date_str = reminder.get('date', '')
            if date_str:
                try:
                    dt = datetime.fromisoformat(date_str)
                    weekday = dt.strftime('%A')
                    patterns['preferred_days'][weekday] = patterns['preferred_days'].get(weekday, 0) + 1
                except:
                    pass

        return patterns

    def recommend_schedule(self, member: str, date: str) -> List[Dict]:
        """Recommend schedule for a specific date"""
        patterns = self.analyze_historical_patterns(member)

        suggestions = []

        # Simple recommendation based on patterns
        if patterns['preferred_times']:
            top_hour = max(patterns['preferred_times'].items(), key=lambda x: x[1])[0]
            suggestions.append({
                'type': 'optimal_time',
                'time': f"{top_hour:02d}:00",
                'reason': f"你在{top_hour}点最活跃"
            })

        return suggestions

    def predict_free_time(self, member: str, date: str) -> List[Dict]:
        """Predict free time slots"""
        # Simplified: return common free time slots
        common_slots = [
            {'start': '09:00', 'end': '11:00', 'probability': 0.8},
            {'start': '14:00', 'end': '16:00', 'probability': 0.7},
            {'start': '19:00', 'end': '21:00', 'probability': 0.9}
        ]
        return common_slots
