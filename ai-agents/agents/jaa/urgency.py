"""
Project Urgency Assessment for JAA
Categorizes projects as Emergency, Week, Month, or Flexible
"""
from datetime import datetime, timedelta
from typing import Any


class UrgencyAssessor:
    """Assesses project urgency based on conversation data"""

    def __init__(self):
        # Keywords that indicate different urgency levels
        self.emergency_keywords = [
            "emergency", "asap", "immediately", "right away",
            "leak", "flooding", "no heat", "no hot water", "electrical issue",
            "dangerous", "safety", "broken", "not working"
        ]
        
        self.urgent_keywords = [
            "urgent", "need quickly", "time sensitive", "can't wait",
            "priority", "high priority", "important", "pressing"
        ]

        self.week_keywords = [
            "this week", "within a week", "soon", "quickly", "fast",
            "need it done", "before", "deadline"
        ]

        self.month_keywords = [
            "this month", "within a month", "month or so", "few weeks",
            "by the end of", "before spring", "before winter"
        ]

        self.flexible_keywords = [
            "flexible", "no rush", "whenever", "planning ahead",
            "future", "eventually", "thinking about", "considering"
        ]

    def assess_urgency(self, project_info: dict[str, Any]) -> str:
        """
        Assess project urgency based on extracted information
        Returns: 'emergency', 'urgent', 'week', 'month', or 'flexible'
        """

        # Check for explicit urgency in collected info
        explicit_urgency = project_info.get("urgency")
        if explicit_urgency and explicit_urgency in ["emergency", "urgent", "week", "month", "flexible"]:
            return explicit_urgency

        # Analyze conversation content for urgency signals
        urgency_signals = self._analyze_urgency_signals(project_info)

        # Assess based on project type and concerns
        type_urgency = self._assess_type_urgency(project_info)

        # Analyze timeline requirements
        timeline_urgency = self._assess_timeline_urgency(project_info)

        # Combine all factors to determine final urgency
        final_urgency = self._determine_final_urgency(
            urgency_signals, type_urgency, timeline_urgency
        )

        return final_urgency

    def _analyze_urgency_signals(self, project_info: dict[str, Any]) -> dict[str, int]:
        """Analyze conversation for urgency-indicating language"""

        # Combine all text data for analysis
        text_sources = []

        # Add requirements and concerns
        requirements = project_info.get("requirements", {})
        concerns = project_info.get("concerns", [])

        if isinstance(requirements, dict):
            text_sources.extend(str(v) for v in requirements.values())

        if isinstance(concerns, list):
            text_sources.extend(concerns)

        # Combine all text
        full_text = " ".join(text_sources).lower()

        # Count urgency keywords
        urgency_scores = {
            "emergency": 0,
            "urgent": 0,
            "week": 0,
            "month": 0,
            "flexible": 0
        }

        for keyword in self.emergency_keywords:
            urgency_scores["emergency"] += full_text.count(keyword.lower())

        for keyword in self.urgent_keywords:
            urgency_scores["urgent"] += full_text.count(keyword.lower())

        for keyword in self.week_keywords:
            urgency_scores["week"] += full_text.count(keyword.lower())

        for keyword in self.month_keywords:
            urgency_scores["month"] += full_text.count(keyword.lower())

        for keyword in self.flexible_keywords:
            urgency_scores["flexible"] += full_text.count(keyword.lower())

        return urgency_scores

    def _assess_type_urgency(self, project_info: dict[str, Any]) -> str:
        """Assess urgency based on project type and concerns"""

        project_type = (project_info.get("project_type", "")).lower()
        concerns = project_info.get("concerns", [])

        # Emergency project types
        emergency_types = [
            "leak", "flooding", "electrical", "heating", "cooling",
            "plumbing emergency", "roof leak", "no hot water"
        ]

        # Emergency concerns
        emergency_concerns = [
            "damage", "leak", "electrical_issue", "structural"
        ]

        # Check for emergency indicators
        if any(emergency_type in project_type for emergency_type in emergency_types):
            return "emergency"

        if any(concern in concerns for concern in emergency_concerns):
            return "emergency"

        # Urgent project types (need attention but not emergency)
        urgent_types = [
            "repair", "fix", "broken", "not working", "important repair"
        ]

        if any(urgent_type in project_type for urgent_type in urgent_types):
            return "urgent"

        # Month-timeline projects (renovations, improvements)
        month_timeline_types = [
            "kitchen", "bathroom", "renovation", "remodel"
        ]

        if any(month_type in project_type for month_type in month_timeline_types):
            return "month"

        # Default to flexible for planning projects
        return "flexible"

    def _assess_timeline_urgency(self, project_info: dict[str, Any]) -> str:
        """Assess urgency based on timeline requirements"""

        timeline_start = project_info.get("timeline_start")
        project_info.get("timeline_end")

        if not timeline_start:
            return "flexible"

        try:
            # Parse timeline start if it's a string
            if isinstance(timeline_start, str):
                # Try to parse common date formats
                start_date = self._parse_date_string(timeline_start)
            else:
                start_date = timeline_start

            if not start_date:
                return "flexible"

            # Calculate days until start
            today = datetime.now().date()
            if hasattr(start_date, "date"):
                start_date = start_date.date()

            days_until_start = (start_date - today).days

            # Categorize based on timeline
            if days_until_start <= 7:
                return "week"
            elif days_until_start <= 30:
                return "month"
            else:
                return "flexible"

        except Exception as e:
            print(f"[UrgencyAssessor] Error parsing timeline: {e}")
            return "flexible"

    def _parse_date_string(self, date_string: str) -> datetime:
        """Parse various date string formats"""

        date_string = date_string.lower().strip()
        today = datetime.now()

        # Handle relative dates
        if "asap" in date_string or "immediately" in date_string:
            return today

        if "this week" in date_string:
            return today + timedelta(days=3)

        if "next week" in date_string:
            return today + timedelta(weeks=1)

        if "this month" in date_string:
            return today + timedelta(days=15)

        if "next month" in date_string:
            return today + timedelta(days=45)

        # Handle season references
        if "spring" in date_string:
            return datetime(today.year, 3, 15)

        if "summer" in date_string:
            return datetime(today.year, 6, 15)

        if "fall" in date_string or "autumn" in date_string:
            return datetime(today.year, 9, 15)

        if "winter" in date_string:
            return datetime(today.year, 12, 15)

        # Try to parse standard date formats
        import dateutil.parser
        try:
            return dateutil.parser.parse(date_string)
        except:
            return None

    def _determine_final_urgency(self, signal_scores: dict[str, int],
                                type_urgency: str, timeline_urgency: str) -> str:
        """Combine all urgency factors to determine final urgency level"""

        # Create urgency priority map
        urgency_priority = {
            "emergency": 5,
            "urgent": 4,
            "week": 3,
            "month": 2,
            "flexible": 1
        }

        # Get highest scoring signal
        signal_urgency = max(signal_scores, key=signal_scores.get) if any(signal_scores.values()) else "flexible"

        # Get highest priority urgency from all factors
        factors = [signal_urgency, type_urgency, timeline_urgency]
        final_urgency = max(factors, key=lambda x: urgency_priority.get(x, 0))

        # Override: if emergency signals are present, always emergency
        if signal_scores.get("emergency", 0) > 0:
            return "emergency"

        # Override: if urgent signals are present, use urgent
        if signal_scores.get("urgent", 0) > 0:
            return "urgent"

        # Override: if explicit week timing mentioned with urgent project
        if signal_scores.get("week", 0) > 0 and type_urgency in ["emergency", "urgent", "week"]:
            return "week"

        return final_urgency

    def get_urgency_description(self, urgency_level: str) -> str:
        """Get human-readable description of urgency level"""

        descriptions = {
            "emergency": "Emergency - Immediate attention required (same day)",
            "urgent": "Urgent - High priority, start within 2-3 days",
            "week": "Week - Start within 1 week",
            "month": "Standard - Start within 1 month",
            "flexible": "Flexible - No specific timeline pressure"
        }

        return descriptions.get(urgency_level, "Unknown urgency level")
