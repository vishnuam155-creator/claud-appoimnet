"""
Natural language date parser for appointment booking
"""
from datetime import datetime, timedelta
import re


class DateParser:
    """Parse natural language dates into datetime objects"""
    
    def __init__(self):
        self.today = datetime.now().date()
    
    def parse(self, text):
        """
        Parse natural language date input
        Returns: datetime.date object or None
        """
        text = text.lower().strip()
        
        # Try different parsing strategies
        parsers = [
            self._parse_relative_day,
            self._parse_specific_date,
            self._parse_month_day,
            self._parse_iso_format
        ]
        
        for parser in parsers:
            result = parser(text)
            if result:
                return result
        
        return None
    
    def _parse_relative_day(self, text):
        """Parse: today, tomorrow, next monday, coming tuesday"""
        
        # Today
        if 'today' in text:
            return self.today
        
        # Tomorrow
        if 'tomorrow' in text:
            return self.today + timedelta(days=1)
        
        # Day after tomorrow
        if 'day after tomorrow' in text:
            return self.today + timedelta(days=2)
        
        # Next week
        if 'next week' in text:
            return self.today + timedelta(days=7)
        
        # Days of the week
        days = {
            'monday': 0, 'mon': 0,
            'tuesday': 1, 'tue': 1, 'tues': 1,
            'wednesday': 2, 'wed': 2,
            'thursday': 3, 'thu': 3, 'thur': 3, 'thurs': 3,
            'friday': 4, 'fri': 4,
            'saturday': 5, 'sat': 5,
            'sunday': 6, 'sun': 6
        }
        
        for day_name, day_num in days.items():
            if day_name in text:
                # Check if it's "next" or "coming"
                if any(word in text for word in ['next', 'coming', 'this']):
                    return self._get_next_weekday(day_num)
        
        return None
    
    def _get_next_weekday(self, target_day):
        """Get the next occurrence of a weekday (0=Monday, 6=Sunday)"""
        current_day = self.today.weekday()
        days_ahead = target_day - current_day
        
        if days_ahead <= 0:  # Target day already passed this week
            days_ahead += 7
        
        return self.today + timedelta(days=days_ahead)
    
    def _parse_specific_date(self, text):
        """Parse: november 3, nov 3, 3 november"""
        months = {
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
        
        # Find month and day
        month_num = None
        day_num = None
        
        for month_name, month_val in months.items():
            if month_name in text:
                month_num = month_val
                # Extract day number near the month
                numbers = re.findall(r'\b(\d{1,2})\b', text)
                if numbers:
                    day_num = int(numbers[0])
                break
        
        if month_num and day_num:
            try:
                year = self.today.year
                # If the date is in the past this year, assume next year
                date = datetime(year, month_num, day_num).date()
                if date < self.today:
                    date = datetime(year + 1, month_num, day_num).date()
                return date
            except ValueError:
                return None
        
        return None
    
    def _parse_month_day(self, text):
        """Parse: 11/3, 11-3, 03/11"""
        # Match patterns like 11/3, 11-3, 11.3
        patterns = [
            r'(\d{1,2})[/-](\d{1,2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    # Try month/day format
                    month = int(match.group(1))
                    day = int(match.group(2))
                    
                    if month > 12:  # Probably day/month format
                        month, day = day, month
                    
                    year = self.today.year
                    date = datetime(year, month, day).date()
                    
                    if date < self.today:
                        date = datetime(year + 1, month, day).date()
                    
                    return date
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _parse_iso_format(self, text):
        """Parse: 2025-11-03, YYYY-MM-DD"""
        try:
            # Find ISO format date
            match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', text)
            if match:
                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))
                return datetime(year, month, day).date()
        except ValueError:
            pass
        
        return None
    
    def is_valid_future_date(self, date):
        """Check if date is in the future and not too far"""
        if not date:
            return False
        
        # Must be today or future
        if date < self.today:
            return False
        
        # Not more than 90 days in future
        max_date = self.today + timedelta(days=90)
        if date > max_date:
            return False
        
        return True


# Quick test function
def test_parser():
    parser = DateParser()
    
    test_cases = [
        "next monday",
        "coming Monday",
        "november 3",
        "nov 3",
        "3 november",
        "tomorrow",
        "11/3",
        "2025-11-03",
        "this friday"
    ]
    
    print("Date Parser Test:")
    for test in test_cases:
        result = parser.parse(test)
        print(f"  '{test}' → {result}")


if __name__ == '__main__':
    test_parser()