"""
Response Parser for EAA
Parse and analyze contractor responses from email and SMS
"""
import re
from datetime import datetime
from typing import Any


class ResponseParser:
    """Parse and analyze contractor responses"""

    def __init__(self):
        """Initialize response parser with sentiment and intent rules"""
        self.positive_keywords = [
            "yes", "interested", "available", "sounds good", "absolutely",
            "definitely", "sure", "count me in", "let's do it", "i'm in",
            "perfect", "great", "excellent", "love to", "would love",
            "happy to", "ready", "can do", "no problem"
        ]

        self.negative_keywords = [
            "no", "not interested", "pass", "decline", "busy", "booked",
            "unavailable", "can't", "cannot", "won't", "will not",
            "not available", "too far", "outside area", "not my specialty",
            "wrong type", "unsubscribe", "stop", "remove"
        ]

        self.info_request_keywords = [
            "more info", "details", "information", "tell me more",
            "what about", "when", "where", "how much", "timeline",
            "schedule", "materials", "specifications", "requirements",
            "questions", "clarification", "need to know"
        ]

        print("[ResponseParser] Initialized with sentiment analysis rules")

    def parse_response(self, response_content: str, channel: str) -> dict[str, Any]:
        """
        Parse contractor response and extract intent, sentiment, and data

        Args:
            response_content: Raw response text
            channel: Communication channel ('email' or 'sms')

        Returns:
            Parsed response with intent, sentiment, and extracted data
        """
        try:
            # Clean and normalize content
            cleaned_content = self._clean_content(response_content)

            # Determine intent
            intent = self._classify_intent(cleaned_content)

            # Calculate sentiment score
            sentiment = self._calculate_sentiment(cleaned_content)

            # Determine interest level
            interest_level = self._determine_interest_level(intent, sentiment)

            # Extract contact information and other data
            extracted_data = self._extract_data(response_content, channel)

            # Get response metadata
            metadata = self._get_response_metadata(response_content, channel)

            result = {
                "intent": intent,
                "sentiment": sentiment,
                "interest_level": interest_level,
                "extracted_data": extracted_data,
                "metadata": metadata,
                "processed_at": datetime.now().isoformat(),
                "confidence_score": self._calculate_confidence(intent, sentiment, cleaned_content)
            }

            print(f"[ResponseParser] Parsed {channel} response: {intent} ({interest_level} interest)")

            return result

        except Exception as e:
            print(f"[ResponseParser ERROR] Failed to parse response: {e}")
            return {
                "intent": "unknown",
                "sentiment": 0.0,
                "interest_level": "unknown",
                "extracted_data": {},
                "metadata": {},
                "error": str(e)
            }

    def _clean_content(self, content: str) -> str:
        """Clean and normalize response content"""
        if not content:
            return ""

        # Convert to lowercase
        cleaned = content.lower().strip()

        # Remove common email artifacts
        cleaned = re.sub(r"on .+ wrote:", "", cleaned)  # Remove email thread headers
        cleaned = re.sub(r">.*$", "", cleaned, flags=re.MULTILINE)  # Remove quoted text
        cleaned = re.sub(r"sent from my.*", "", cleaned)  # Remove mobile signatures

        # Remove extra whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        return cleaned

    def _classify_intent(self, content: str) -> str:
        """Classify the intent of the response"""
        if not content:
            return "no_response"

        # Check for explicit positive responses
        if any(keyword in content for keyword in ["yes", "y", "yeah", "yep", "sure"]):
            return "interested"

        # Check for explicit negative responses
        if any(keyword in content for keyword in ["no", "n", "nope", "not interested", "pass"]):
            return "not_interested"

        # Check for information requests
        if any(keyword in content for keyword in self.info_request_keywords):
            return "need_info"

        # Check for opt-out requests
        if any(keyword in content for keyword in ["stop", "unsubscribe", "remove", "opt out"]):
            return "opt_out"

        # Check based on positive/negative keyword density
        positive_count = sum(1 for keyword in self.positive_keywords if keyword in content)
        negative_count = sum(1 for keyword in self.negative_keywords if keyword in content)

        if positive_count > negative_count and positive_count > 0:
            return "interested"
        elif negative_count > positive_count and negative_count > 0:
            return "not_interested"
        elif positive_count == 0 and negative_count == 0:
            return "neutral"
        else:
            return "mixed"

    def _calculate_sentiment(self, content: str) -> float:
        """Calculate sentiment score from -1.0 (negative) to 1.0 (positive)"""
        if not content:
            return 0.0

        words = content.split()
        total_words = len(words)

        if total_words == 0:
            return 0.0

        # Count positive and negative words
        positive_count = sum(1 for word in words if any(keyword in word for keyword in self.positive_keywords))
        negative_count = sum(1 for word in words if any(keyword in word for keyword in self.negative_keywords))

        # Calculate sentiment score
        sentiment_score = (positive_count - negative_count) / total_words

        # Normalize to -1.0 to 1.0 range
        return max(-1.0, min(1.0, sentiment_score * 5))  # Amplify the score

    def _determine_interest_level(self, intent: str, sentiment: float) -> str:
        """Determine overall interest level"""
        if intent == "interested" or (intent == "mixed" and sentiment > 0.3):
            return "high"
        elif intent == "need_info" or (intent == "neutral" and sentiment >= -0.1):
            return "medium"
        elif intent == "not_interested" or sentiment < -0.3:
            return "low"
        elif intent == "opt_out":
            return "opt_out"
        else:
            return "unknown"

    def _extract_data(self, content: str, channel: str) -> dict[str, Any]:
        """Extract useful data from response content"""
        extracted = {}

        # Extract phone numbers
        phone_pattern = r"\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b"
        phone_matches = re.findall(phone_pattern, content)
        if phone_matches:
            extracted["phone_numbers"] = [f"({m[0]}) {m[1]}-{m[2]}" for m in phone_matches]

        # Extract email addresses
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        email_matches = re.findall(email_pattern, content)
        if email_matches:
            extracted["email_addresses"] = email_matches

        # Extract availability mentions
        availability_keywords = ["available", "free", "open", "busy", "booked"]
        availability_mentions = [word for word in content.split() if any(keyword in word.lower() for keyword in availability_keywords)]
        if availability_mentions:
            extracted["availability_mentions"] = availability_mentions

        # Extract time-related information
        time_pattern = r"\b(?:next|this)\s+(?:week|month|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b"
        time_matches = re.findall(time_pattern, content, re.IGNORECASE)
        if time_matches:
            extracted["time_references"] = time_matches

        # Extract questions or concerns
        question_pattern = r"[^.!?]*\?[^.!?]*"
        questions = re.findall(question_pattern, content)
        if questions:
            extracted["questions"] = [q.strip() for q in questions]

        # Extract company/business mentions
        business_pattern = r"\b(?:LLC|Inc|Corp|Company|Construction|Builders?)\b"
        business_matches = re.findall(business_pattern, content, re.IGNORECASE)
        if business_matches:
            extracted["business_mentions"] = business_matches

        return extracted

    def _get_response_metadata(self, content: str, channel: str) -> dict[str, Any]:
        """Get metadata about the response"""
        metadata = {
            "channel": channel,
            "length": len(content),
            "word_count": len(content.split()),
            "has_questions": "?" in content,
            "has_exclamations": "!" in content,
            "response_time_category": self._categorize_response_time(),
            "language_detected": "en"  # Default to English for now
        }

        # Channel-specific metadata
        if channel == "email":
            metadata["likely_mobile"] = any(signature in content.lower() for signature in
                                          ["sent from my", "sent via", "from my iphone", "from my android"])
        elif channel == "sms":
            metadata["character_count"] = len(content)
            metadata["likely_abbreviated"] = len(content) < 20 or any(abbrev in content.lower() for abbrev in
                                                                    ["u", "ur", "r", "y", "n", "thx", "k"])

        return metadata

    def _categorize_response_time(self) -> str:
        """Categorize response time (placeholder - would use actual timing in production)"""
        # In production, this would compare response time to send time
        return "immediate"  # immediate, fast, normal, slow

    def _calculate_confidence(self, intent: str, sentiment: float, content: str) -> float:
        """Calculate confidence score in the parsing results"""
        confidence = 50.0  # Base confidence

        # Higher confidence for clear intent
        if intent in ["interested", "not_interested"]:
            confidence += 30.0
        elif intent == "need_info":
            confidence += 20.0
        elif intent == "neutral":
            confidence += 10.0

        # Higher confidence for strong sentiment
        abs_sentiment = abs(sentiment)
        confidence += abs_sentiment * 15

        # Higher confidence for longer responses
        word_count = len(content.split())
        if word_count > 5:
            confidence += 10.0
        elif word_count > 10:
            confidence += 20.0

        return min(100.0, confidence)

    def get_follow_up_suggestion(self, parsed_response: dict[str, Any]) -> dict[str, Any]:
        """Suggest follow-up actions based on parsed response"""
        intent = parsed_response.get("intent")
        interest_level = parsed_response.get("interest_level")
        extracted_data = parsed_response.get("extracted_data", {})

        if intent == "interested" or interest_level == "high":
            return {
                "action": "initiate_onboarding",
                "priority": "high",
                "message": "Contractor expressed interest - start onboarding process",
                "next_step": "Send onboarding welcome email"
            }

        elif intent == "need_info" or interest_level == "medium":
            questions = extracted_data.get("questions", [])
            return {
                "action": "send_additional_info",
                "priority": "medium",
                "message": f"Contractor has questions: {questions}" if questions else "Contractor needs more information",
                "next_step": "Send detailed project information or schedule call"
            }

        elif intent == "not_interested" or interest_level == "low":
            return {
                "action": "mark_not_interested",
                "priority": "low",
                "message": "Contractor not interested in this project",
                "next_step": "Add to exclusion list for similar projects"
            }

        elif intent == "opt_out":
            return {
                "action": "process_opt_out",
                "priority": "high",
                "message": "Contractor requested to opt out",
                "next_step": "Add to opt-out list and confirm"
            }

        else:
            return {
                "action": "manual_review",
                "priority": "medium",
                "message": "Response unclear - needs manual review",
                "next_step": "Human review of response content"
            }
