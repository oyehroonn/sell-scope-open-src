"""Predictive Demand Engine - Forecasting and trend detection"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import math
import structlog

logger = structlog.get_logger()


SEASONAL_EVENTS = {
    "new_years": {
        "name": "New Year's",
        "month": 1,
        "day": 1,
        "lead_time_days": 45,
        "duration_days": 14,
        "keywords": ["new year", "celebration", "fireworks", "champagne", "midnight", "countdown"],
        "demand_multiplier": 1.5,
    },
    "valentines": {
        "name": "Valentine's Day",
        "month": 2,
        "day": 14,
        "lead_time_days": 30,
        "duration_days": 7,
        "keywords": ["valentine", "love", "heart", "romantic", "couple", "red", "roses"],
        "demand_multiplier": 1.8,
    },
    "easter": {
        "name": "Easter",
        "month": 4,
        "day": 15,
        "lead_time_days": 30,
        "duration_days": 14,
        "keywords": ["easter", "spring", "bunny", "eggs", "pastel", "flowers"],
        "demand_multiplier": 1.4,
    },
    "mothers_day": {
        "name": "Mother's Day",
        "month": 5,
        "day": 12,
        "lead_time_days": 21,
        "duration_days": 7,
        "keywords": ["mother", "mom", "family", "flowers", "gift", "love"],
        "demand_multiplier": 1.3,
    },
    "fathers_day": {
        "name": "Father's Day",
        "month": 6,
        "day": 16,
        "lead_time_days": 21,
        "duration_days": 7,
        "keywords": ["father", "dad", "family", "gift", "tools", "golf"],
        "demand_multiplier": 1.2,
    },
    "summer": {
        "name": "Summer Season",
        "month": 6,
        "day": 21,
        "lead_time_days": 45,
        "duration_days": 90,
        "keywords": ["summer", "beach", "vacation", "sun", "travel", "outdoor"],
        "demand_multiplier": 1.3,
    },
    "back_to_school": {
        "name": "Back to School",
        "month": 8,
        "day": 15,
        "lead_time_days": 45,
        "duration_days": 30,
        "keywords": ["school", "education", "student", "classroom", "learning", "backpack"],
        "demand_multiplier": 1.6,
    },
    "halloween": {
        "name": "Halloween",
        "month": 10,
        "day": 31,
        "lead_time_days": 45,
        "duration_days": 14,
        "keywords": ["halloween", "spooky", "pumpkin", "costume", "scary", "witch"],
        "demand_multiplier": 1.7,
    },
    "thanksgiving": {
        "name": "Thanksgiving",
        "month": 11,
        "day": 28,
        "lead_time_days": 30,
        "duration_days": 7,
        "keywords": ["thanksgiving", "turkey", "autumn", "fall", "family", "harvest"],
        "demand_multiplier": 1.5,
    },
    "black_friday": {
        "name": "Black Friday",
        "month": 11,
        "day": 29,
        "lead_time_days": 30,
        "duration_days": 7,
        "keywords": ["shopping", "sale", "discount", "retail", "black friday", "deals"],
        "demand_multiplier": 1.8,
    },
    "christmas": {
        "name": "Christmas",
        "month": 12,
        "day": 25,
        "lead_time_days": 60,
        "duration_days": 21,
        "keywords": ["christmas", "holiday", "winter", "snow", "gift", "tree", "santa"],
        "demand_multiplier": 2.0,
    },
}

MACRO_TRENDS = {
    "remote_work": {
        "name": "Remote Work",
        "keywords": ["remote", "work from home", "home office", "telecommute", "hybrid work"],
        "growth_rate": 0.15,
        "peak_year": 2024,
    },
    "ai_technology": {
        "name": "AI & Technology",
        "keywords": ["artificial intelligence", "ai", "machine learning", "automation", "tech"],
        "growth_rate": 0.25,
        "peak_year": None,
    },
    "sustainability": {
        "name": "Sustainability",
        "keywords": ["eco-friendly", "sustainable", "green", "environment", "renewable"],
        "growth_rate": 0.12,
        "peak_year": None,
    },
    "wellness": {
        "name": "Wellness & Mental Health",
        "keywords": ["wellness", "mental health", "meditation", "mindfulness", "self-care"],
        "growth_rate": 0.18,
        "peak_year": None,
    },
    "diversity": {
        "name": "Diversity & Inclusion",
        "keywords": ["diversity", "inclusion", "multicultural", "equality", "representation"],
        "growth_rate": 0.10,
        "peak_year": None,
    },
}


class PredictiveEngine:
    """Predict demand patterns and trends"""
    
    def __init__(self):
        self.current_date = datetime.now()
    
    def get_upcoming_events(self, days_ahead: int = 90) -> List[Dict[str, Any]]:
        """Get upcoming seasonal events within the specified timeframe"""
        upcoming = []
        
        for event_id, event in SEASONAL_EVENTS.items():
            event_date = datetime(
                self.current_date.year,
                event["month"],
                event["day"],
            )
            
            if event_date < self.current_date:
                event_date = datetime(
                    self.current_date.year + 1,
                    event["month"],
                    event["day"],
                )
            
            days_until = (event_date - self.current_date).days
            
            if days_until <= days_ahead:
                upload_deadline = max(0, days_until - event["lead_time_days"])
                
                urgency = "low"
                if upload_deadline <= 7:
                    urgency = "critical"
                elif upload_deadline <= 14:
                    urgency = "high"
                elif upload_deadline <= 30:
                    urgency = "medium"
                
                upcoming.append({
                    "event_id": event_id,
                    "name": event["name"],
                    "date": event_date.isoformat(),
                    "days_until": days_until,
                    "upload_deadline_days": upload_deadline,
                    "urgency": urgency,
                    "keywords": event["keywords"],
                    "demand_multiplier": event["demand_multiplier"],
                })
        
        return sorted(upcoming, key=lambda x: x["days_until"])
    
    def predict_keyword_demand(self, keyword: str) -> Dict[str, Any]:
        """Predict demand for a keyword based on seasonality and trends"""
        keyword_lower = keyword.lower()
        
        base_demand = 50.0
        seasonal_boost = 0.0
        trend_boost = 0.0
        matching_events = []
        matching_trends = []
        
        for event_id, event in SEASONAL_EVENTS.items():
            for event_keyword in event["keywords"]:
                if event_keyword in keyword_lower:
                    event_date = datetime(
                        self.current_date.year,
                        event["month"],
                        event["day"],
                    )
                    if event_date < self.current_date:
                        event_date = datetime(
                            self.current_date.year + 1,
                            event["month"],
                            event["day"],
                        )
                    
                    days_until = (event_date - self.current_date).days
                    
                    if days_until <= event["lead_time_days"] + event["duration_days"]:
                        boost = (event["demand_multiplier"] - 1) * 50
                        proximity_factor = max(0, 1 - days_until / (event["lead_time_days"] + event["duration_days"]))
                        seasonal_boost = max(seasonal_boost, boost * proximity_factor)
                        matching_events.append({
                            "event": event["name"],
                            "days_until": days_until,
                            "boost": boost * proximity_factor,
                        })
                    break
        
        for trend_id, trend in MACRO_TRENDS.items():
            for trend_keyword in trend["keywords"]:
                if trend_keyword in keyword_lower:
                    boost = trend["growth_rate"] * 100
                    trend_boost = max(trend_boost, boost)
                    matching_trends.append({
                        "trend": trend["name"],
                        "growth_rate": trend["growth_rate"],
                        "boost": boost,
                    })
                    break
        
        predicted_demand = min(100, base_demand + seasonal_boost + trend_boost)
        
        forecast_window = 30
        forecast = []
        for days in range(0, forecast_window, 7):
            future_date = self.current_date + timedelta(days=days)
            future_demand = base_demand + trend_boost
            
            for event_id, event in SEASONAL_EVENTS.items():
                for event_keyword in event["keywords"]:
                    if event_keyword in keyword_lower:
                        event_date = datetime(
                            future_date.year,
                            event["month"],
                            event["day"],
                        )
                        if event_date < future_date:
                            event_date = datetime(
                                future_date.year + 1,
                                event["month"],
                                event["day"],
                            )
                        
                        days_until = (event_date - future_date).days
                        if days_until <= event["lead_time_days"] + event["duration_days"]:
                            boost = (event["demand_multiplier"] - 1) * 50
                            proximity_factor = max(0, 1 - days_until / (event["lead_time_days"] + event["duration_days"]))
                            future_demand += boost * proximity_factor
                        break
            
            forecast.append({
                "date": future_date.isoformat(),
                "demand": min(100, future_demand),
            })
        
        recommendation = "standard"
        if seasonal_boost > 30:
            recommendation = "urgent_seasonal"
        elif trend_boost > 15:
            recommendation = "trending"
        elif predicted_demand > 70:
            recommendation = "high_demand"
        
        return {
            "keyword": keyword,
            "current_demand": predicted_demand,
            "seasonal_boost": seasonal_boost,
            "trend_boost": trend_boost,
            "matching_events": matching_events,
            "matching_trends": matching_trends,
            "forecast": forecast,
            "recommendation": recommendation,
            "best_upload_window": self._calculate_best_window(matching_events),
        }
    
    def _calculate_best_window(self, events: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Calculate the best upload window based on events"""
        if not events:
            return None
        
        soonest = min(events, key=lambda x: x["days_until"])
        upload_by = max(0, soonest["days_until"] - 14)
        
        return {
            "upload_by_days": upload_by,
            "target_event": soonest["event"],
            "reason": f"Upload before {soonest['event']} to maximize visibility",
        }
    
    def get_content_calendar(self, months_ahead: int = 3) -> List[Dict[str, Any]]:
        """Generate a content calendar for the next N months"""
        calendar = []
        
        for month_offset in range(months_ahead):
            future_date = self.current_date + timedelta(days=month_offset * 30)
            month = future_date.month
            year = future_date.year
            
            month_events = []
            for event_id, event in SEASONAL_EVENTS.items():
                if event["month"] == month or event["month"] == (month % 12) + 1:
                    month_events.append({
                        "event_id": event_id,
                        "name": event["name"],
                        "keywords": event["keywords"],
                        "demand_multiplier": event["demand_multiplier"],
                    })
            
            calendar.append({
                "year": year,
                "month": month,
                "month_name": future_date.strftime("%B"),
                "events": month_events,
                "recommended_focus": self._get_month_focus(month),
            })
        
        return calendar
    
    def _get_month_focus(self, month: int) -> str:
        """Get recommended content focus for a month"""
        focus_map = {
            1: "New Year, winter, fitness/wellness goals",
            2: "Valentine's Day, love, romance",
            3: "Spring, St. Patrick's Day, renewal",
            4: "Easter, spring activities, outdoor",
            5: "Mother's Day, flowers, family",
            6: "Summer, Father's Day, vacation prep",
            7: "Summer activities, beach, travel",
            8: "Back to school, late summer",
            9: "Fall, autumn, back to work",
            10: "Halloween, autumn colors",
            11: "Thanksgiving, Black Friday, pre-holiday",
            12: "Christmas, holidays, winter",
        }
        return focus_map.get(month, "General content")


async def predict_demand(keyword: str) -> Dict[str, Any]:
    """Main entry point for demand prediction"""
    engine = PredictiveEngine()
    return engine.predict_keyword_demand(keyword)


async def get_content_calendar(months: int = 3) -> List[Dict[str, Any]]:
    """Get content calendar"""
    engine = PredictiveEngine()
    return engine.get_content_calendar(months)


async def get_upcoming_events(days: int = 90) -> List[Dict[str, Any]]:
    """Get upcoming seasonal events"""
    engine = PredictiveEngine()
    return engine.get_upcoming_events(days)
