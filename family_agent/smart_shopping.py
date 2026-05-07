"""
Smart Shopping Advisor
Analyzes consumption patterns and provides smart suggestions
"""
from typing import List, Dict
from datetime import datetime, timedelta
from pathlib import Path
import json


class SmartShoppingAdvisor:
    """Smart shopping advisor based on consumption patterns"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.shopping_file = self.data_dir / "shopping_list.json"
        self.history_file = self.data_dir / "shopping_history.json"
        self._load_history()

    def _load_history(self):
        """Load shopping history"""
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                self.history = json.load(f)
        else:
            self.history = []

    def _save_history(self):
        """Save shopping history"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def analyze_consumption_patterns(self) -> Dict:
        """
        Analyze historical consumption patterns
        Returns: {item_name: {'avg_days': int, 'last_purchase': str, 'frequency': int}}
        """
        patterns = {}
        for record in self.history:
            item = record['name']
            if item not in patterns:
                patterns[item] = {
                    'purchase_dates': [],
                    'avg_days': 0,
                    'frequency': 0
                }
            patterns[item]['purchase_dates'].append(record['date'])
            patterns[item]['frequency'] += 1

        # Calculate average days between purchases
        for item, data in patterns.items():
            dates = sorted(data['purchase_dates'])
            if len(dates) >= 2:
                deltas = []
                for i in range(1, len(dates)):
                    d1 = datetime.fromisoformat(dates[i-1])
                    d2 = datetime.fromisoformat(dates[i])
                    deltas.append((d2 - d1).days)
                data['avg_days'] = sum(deltas) // len(deltas) if deltas else 0

        return patterns

    def predict_reorder_items(self) -> List[Dict]:
        """
        Predict items that need reordering
        Returns: [{'name': str, 'days_since': int, 'urgency': str}]
        """
        patterns = self.analyze_consumption_patterns()
        predictions = []
        today = datetime.now()

        for item, data in patterns.items():
            if not data['purchase_dates']:
                continue
            last_date = datetime.fromisoformat(max(data['purchase_dates']))
            days_since = (today - last_date).days

            # Predict based on average days
            if data['avg_days'] > 0 and days_since >= data['avg_days'] * 0.8:
                urgency = 'high' if days_since >= data['avg_days'] else 'normal'
                predictions.append({
                    'name': item,
                    'days_since': days_since,
                    'avg_interval': data['avg_days'],
                    'urgency': urgency
                })

        return sorted(predictions, key=lambda x: x['days_since'], reverse=True)

    def generate_shopping_suggestions(self, member: str) -> List[Dict]:
        """Generate personalized shopping suggestions"""
        reorder = self.predict_reorder_items()

        # Add suggestions based on member preferences (simplified)
        suggestions = []
        for item in reorder:
            suggestions.append({
                'type': 'reorder',
                'item': item['name'],
                'reason': f"{item['days_since']}天未购买，建议补货",
                'urgency': item['urgency']
            })

        return suggestions

    def record_purchase(self, item_name: str, quantity: str, member: str):
        """Record a purchase to history"""
        self.history.append({
            'name': item_name,
            'quantity': quantity,
            'member': member,
            'date': datetime.now().isoformat()
        })
        self._save_history()
