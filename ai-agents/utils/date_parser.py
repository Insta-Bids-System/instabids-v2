"""
Simple Date Parser for Exact Date Extraction
Handles natural language dates like "by Friday", "before Christmas", "wedding June 15th"
"""
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import calendar


class SimpleDateParser:
    """Simple date parser for deadline extraction"""
    
    def __init__(self):
        # Common date patterns
        self.month_names = {
            'january': 1, 'jan': 1,
            'february': 2, 'feb': 2,
            'march': 3, 'mar': 3,
            'april': 4, 'apr': 4,
            'may': 5,
            'june': 6, 'jun': 6,
            'july': 7, 'jul': 7,
            'august': 8, 'aug': 8,
            'september': 9, 'sep': 9, 'sept': 9,
            'october': 10, 'oct': 10,
            'november': 11, 'nov': 11,
            'december': 12, 'dec': 12
        }
        
        self.day_names = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        # Holiday mappings (simplified)
        self.holidays = {
            'christmas': (12, 25),
            'new years': (1, 1),
            'thanksgiving': None,  # Complex calculation
            'easter': None,        # Complex calculation
        }

    def parse_natural_language_date(self, text: str, context_date: Optional[datetime] = None) -> Dict:
        """
        Parse natural language into exact dates
        
        Args:
            text: Natural language text like "by Friday" or "wedding June 15th"
            context_date: Reference date (defaults to today)
            
        Returns:
            dict with parsed_date, deadline_hard, deadline_context
        """
        if context_date is None:
            context_date = datetime.now()
            
        text_lower = text.lower().strip()
        
        result = {
            'parsed_date': None,
            'deadline_hard': False,
            'deadline_context': text,
            'confidence': 0.0
        }
        
        # Pattern 1: "by Friday", "before Christmas" 
        if 'by ' in text_lower or 'before ' in text_lower:
            result['deadline_hard'] = True
            date_part = text_lower.replace('by ', '').replace('before ', '')
            parsed_date = self._parse_relative_date(date_part, context_date)
            if parsed_date:
                result['parsed_date'] = parsed_date
                result['confidence'] = 0.9
                
        # Pattern 2: "wedding June 15th", "graduation May 20"
        elif any(event in text_lower for event in ['wedding', 'graduation', 'party', 'event']):
            result['deadline_hard'] = True
            parsed_date = self._parse_month_day(text_lower, context_date)
            if parsed_date:
                result['parsed_date'] = parsed_date
                result['confidence'] = 0.95
                
        # Pattern 3: Direct dates "June 15th", "12/25", "2025-06-15"
        else:
            parsed_date = self._parse_direct_date(text_lower, context_date)
            if parsed_date:
                result['parsed_date'] = parsed_date
                result['confidence'] = 0.8
                result['deadline_hard'] = 'asap' in text_lower or 'urgent' in text_lower
        
        return result

    def _parse_relative_date(self, date_text: str, context_date: datetime) -> Optional[datetime]:
        """Parse relative dates like 'friday', 'next month', 'christmas'"""
        
        # Day of week
        for day_name, day_num in self.day_names.items():
            if day_name in date_text:
                days_ahead = day_num - context_date.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                return context_date + timedelta(days=days_ahead)
        
        # Holidays
        for holiday_name, date_tuple in self.holidays.items():
            if holiday_name in date_text and date_tuple:
                month, day = date_tuple
                year = context_date.year
                holiday_date = datetime(year, month, day)
                if holiday_date < context_date:
                    holiday_date = datetime(year + 1, month, day)
                return holiday_date
        
        # Next week/month patterns
        if 'next week' in date_text:
            return context_date + timedelta(weeks=1)
        elif 'next month' in date_text:
            next_month = context_date.month + 1
            year = context_date.year
            if next_month > 12:
                next_month = 1
                year += 1
            return datetime(year, next_month, 1)
            
        return None

    def _parse_month_day(self, text: str, context_date: datetime) -> Optional[datetime]:
        """Parse month/day combinations like 'june 15th', 'march 3rd'"""
        
        # Look for month names followed by numbers
        for month_name, month_num in self.month_names.items():
            if month_name in text:
                # Find number after month name
                pattern = rf'{month_name}\s+(\d{{1,2}})'
                match = re.search(pattern, text)
                if match:
                    day = int(match.group(1))
                    year = context_date.year
                    
                    try:
                        result_date = datetime(year, month_num, day)
                        # If date is in the past, assume next year
                        if result_date < context_date:
                            result_date = datetime(year + 1, month_num, day)
                        return result_date
                    except ValueError:
                        continue
        
        return None

    def _parse_direct_date(self, text: str, context_date: datetime) -> Optional[datetime]:
        """Parse direct date formats like '6/15', '2025-06-15', 'June 15'"""
        
        # ISO format: 2025-06-15
        iso_match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', text)
        if iso_match:
            year, month, day = map(int, iso_match.groups())
            try:
                return datetime(year, month, day)
            except ValueError:
                pass
        
        # US format: 6/15 or 06/15/2025
        us_match = re.search(r'(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?', text)
        if us_match:
            month, day = map(int, us_match.groups()[:2])
            year = int(us_match.group(3)) if us_match.group(3) else context_date.year
            if year < 100:  # 2-digit year
                year += 2000
            try:
                result_date = datetime(year, month, day)
                if result_date < context_date and us_match.group(3) is None:
                    result_date = datetime(year + 1, month, day)
                return result_date
            except ValueError:
                pass
        
        return None

    def calculate_bid_collection_deadline(self, project_deadline: datetime, urgency: str = None) -> datetime:
        """
        Calculate when to stop collecting bids based on project deadline
        Simple rule: Stop collecting bids 1-3 days before project deadline
        """
        if urgency == "emergency":
            # Emergency: collect bids up to 4 hours before
            return project_deadline - timedelta(hours=4)
        elif urgency == "week":
            # Week projects: stop 1 day before
            return project_deadline - timedelta(days=1)
        else:
            # Month/flexible: stop 2-3 days before to allow planning
            return project_deadline - timedelta(days=2)

    def determine_campaign_duration(self, project_deadline: datetime, context_date: Optional[datetime] = None) -> str:
        """
        Simple campaign duration calculation based on deadline proximity
        
        Returns: "emergency", "week", "month", or "flexible"
        """
        if context_date is None:
            context_date = datetime.now()
            
        days_available = (project_deadline - context_date).days
        
        if days_available <= 3:
            return "emergency"  # 6 hours
        elif days_available <= 7:
            return "week"      # 1-2 days
        elif days_available <= 14:
            return "month"     # 3-5 days
        else:
            return "flexible"  # 5+ days


# Test the parser
if __name__ == "__main__":
    parser = SimpleDateParser()
    
    test_cases = [
        "by Friday",
        "before Christmas", 
        "wedding June 15th",
        "need it done by 6/15",
        "graduation May 20",
        "next week sometime"
    ]
    
    for case in test_cases:
        result = parser.parse_natural_language_date(case)
        print(f"'{case}' → {result}")