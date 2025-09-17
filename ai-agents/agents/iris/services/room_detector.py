"""
IRIS Room Detector Service
Improved room detection with confidence scoring and user confirmation
"""

import logging
import re
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RoomDetectionResult:
    """Room detection result with confidence scoring"""
    room_type: str
    confidence: float
    detected_keywords: List[str]
    alternative_rooms: List[Tuple[str, float]]  # (room_type, confidence)
    needs_confirmation: bool

class RoomDetector:
    """Detects room types from user messages with improved confidence scoring"""
    
    def __init__(self):
        # Room type mappings with keywords and confidence weights
        self.room_mappings = {
            "kitchen": {
                "keywords": [
                    ("kitchen", 1.0),
                    ("cabinet", 0.8), ("cabinets", 0.8),
                    ("countertop", 0.8), ("countertops", 0.8),
                    ("island", 0.7), ("backsplash", 0.7),
                    ("appliance", 0.6), ("appliances", 0.6),
                    ("stove", 0.7), ("oven", 0.7), ("fridge", 0.7),
                    ("dishwasher", 0.6), ("pantry", 0.6),
                    ("sink", 0.5)  # Lower because could be bathroom
                ],
                "room_type": "kitchen"
            },
            "bathroom": {
                "keywords": [
                    ("bathroom", 1.0), ("bath", 0.9),
                    ("shower", 0.8), ("tub", 0.7), ("bathtub", 0.8),
                    ("toilet", 0.9), ("vanity", 0.8),
                    ("tile", 0.4), ("tiles", 0.4),  # Lower because could be kitchen
                    ("fixture", 0.5), ("fixtures", 0.5),
                    ("mirror", 0.3)  # Very low, could be anywhere
                ],
                "room_type": "bathroom"
            },
            "bedroom": {
                "keywords": [
                    ("bedroom", 1.0), ("bed", 0.7),
                    ("master bedroom", 1.0), ("guest bedroom", 1.0),
                    ("closet", 0.6), ("dresser", 0.7),
                    ("nightstand", 0.8), ("headboard", 0.8),
                    ("mattress", 0.7), ("bedding", 0.6)
                ],
                "room_type": "bedroom"
            },
            "living_room": {
                "keywords": [
                    ("living room", 1.0), ("living", 0.6),
                    ("family room", 1.0), ("great room", 1.0),
                    ("sofa", 0.7), ("couch", 0.7),
                    ("fireplace", 0.8), ("mantle", 0.7),
                    ("entertainment", 0.6), ("tv", 0.4),
                    ("sectional", 0.7)
                ],
                "room_type": "living_room"
            },
            "dining_room": {
                "keywords": [
                    ("dining room", 1.0), ("dining", 0.7),
                    ("table", 0.3), ("chairs", 0.3),  # Very common words
                    ("chandelier", 0.7), ("buffet", 0.8),
                    ("china cabinet", 0.9)
                ],
                "room_type": "dining_room"
            },
            "backyard": {
                "keywords": [
                    ("backyard", 1.0), ("back yard", 1.0),
                    ("patio", 0.8), ("deck", 0.7),
                    ("garden", 0.6), ("landscaping", 0.7),
                    ("outdoor", 0.4), ("outside", 0.3),
                    ("pool", 0.8), ("hot tub", 0.7),
                    ("fence", 0.5), ("lawn", 0.6),
                    ("grass", 0.4), ("turf", 0.6)
                ],
                "room_type": "backyard"
            },
            "front_yard": {
                "keywords": [
                    ("front yard", 1.0), ("frontyard", 1.0),
                    ("curb appeal", 1.0), ("driveway", 0.8),
                    ("walkway", 0.7), ("front door", 0.6),
                    ("entry", 0.4), ("entrance", 0.5),
                    ("mailbox", 0.8), ("sidewalk", 0.6)
                ],
                "room_type": "front_yard"
            },
            "office": {
                "keywords": [
                    ("office", 1.0), ("study", 0.8),
                    ("desk", 0.6), ("workspace", 0.8),
                    ("home office", 1.0), ("den", 0.7),
                    ("library", 0.7), ("computer", 0.3)
                ],
                "room_type": "office"
            },
            "laundry_room": {
                "keywords": [
                    ("laundry", 1.0), ("laundry room", 1.0),
                    ("washer", 0.9), ("dryer", 0.9),
                    ("utility", 0.6), ("utility room", 0.8),
                    ("mudroom", 0.7), ("mud room", 0.7)
                ],
                "room_type": "laundry_room"
            }
        }
        
        # Confidence thresholds
        self.HIGH_CONFIDENCE_THRESHOLD = 0.8
        self.MEDIUM_CONFIDENCE_THRESHOLD = 0.5
        self.MIN_CONFIDENCE_THRESHOLD = 0.3
    
    def detect_room_from_message(self, message: str) -> RoomDetectionResult:
        """
        Detect room type from user message with confidence scoring
        
        Returns:
            RoomDetectionResult with room_type, confidence, and alternatives
        """
        message_lower = message.lower()
        
        # Score all room types
        room_scores = {}
        detected_keywords_per_room = {}
        
        for room_category, room_data in self.room_mappings.items():
            total_score = 0
            detected_keywords = []
            
            for keyword, weight in room_data["keywords"]:
                if keyword.lower() in message_lower:
                    # Count occurrences and apply weight
                    occurrences = len(re.findall(r'\b' + re.escape(keyword.lower()) + r'\b', message_lower))
                    score = weight * occurrences
                    total_score += score
                    detected_keywords.append(keyword)
            
            if total_score > 0:
                room_scores[room_data["room_type"]] = total_score
                detected_keywords_per_room[room_data["room_type"]] = detected_keywords
        
        # No keywords detected
        if not room_scores:
            return RoomDetectionResult(
                room_type="general",
                confidence=0.0,
                detected_keywords=[],
                alternative_rooms=[],
                needs_confirmation=True
            )
        
        # Sort by score (descending)
        sorted_rooms = sorted(room_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Best match
        best_room, best_score = sorted_rooms[0]
        
        # Normalize confidence (cap at 1.0)
        confidence = min(best_score / 2.0, 1.0)  # Divide by 2 to normalize
        
        # Get alternative rooms (top 3 excluding best)
        alternatives = []
        for room, score in sorted_rooms[1:4]:
            alt_confidence = min(score / 2.0, 1.0)
            if alt_confidence >= self.MIN_CONFIDENCE_THRESHOLD:
                alternatives.append((room, alt_confidence))
        
        # Determine if confirmation is needed
        needs_confirmation = (
            confidence < self.HIGH_CONFIDENCE_THRESHOLD or  # Low confidence
            (len(alternatives) > 0 and alternatives[0][1] > confidence * 0.7)  # Close alternatives
        )
        
        return RoomDetectionResult(
            room_type=best_room,
            confidence=confidence,
            detected_keywords=detected_keywords_per_room.get(best_room, []),
            alternative_rooms=alternatives,
            needs_confirmation=needs_confirmation
        )
    
    def generate_confirmation_message(self, detection_result: RoomDetectionResult) -> str:
        """Generate user-friendly confirmation message"""
        
        if detection_result.confidence == 0.0:
            return (
                "I couldn't automatically detect which room these images are for. "
                "Could you let me know which space you're working on? For example: "
                "kitchen, bathroom, bedroom, living room, backyard, etc."
            )
        
        room_display = detection_result.room_type.replace('_', ' ').title()
        
        if detection_result.confidence >= self.HIGH_CONFIDENCE_THRESHOLD:
            # High confidence, just confirm
            return (
                f"I detected this is for your {room_display} based on your message. "
                f"Is that correct?"
            )
        
        elif detection_result.alternative_rooms:
            # Medium confidence with alternatives
            alternatives = [alt[0].replace('_', ' ').title() for alt in detection_result.alternative_rooms[:2]]
            alt_text = " or ".join(alternatives)
            
            return (
                f"I think this might be for your {room_display}, but it could also be "
                f"for your {alt_text}. Which room are you working on?"
            )
        
        else:
            # Medium confidence, no strong alternatives
            return (
                f"I think this might be for your {room_display}, but I'm not completely sure. "
                f"Could you confirm which room you're working on?"
            )
    
    def get_room_suggestions(self) -> List[str]:
        """Get list of supported room types for suggestions"""
        room_types = []
        for room_data in self.room_mappings.values():
            room_type = room_data["room_type"].replace('_', ' ').title()
            room_types.append(room_type)
        
        return sorted(set(room_types))
    
    def parse_user_room_selection(self, user_response: str) -> Optional[str]:
        """Parse user's room selection response"""
        user_response_lower = user_response.lower().strip()
        
        # Direct matching first
        for room_data in self.room_mappings.values():
            room_type = room_data["room_type"]
            if room_type.lower() in user_response_lower:
                return room_type
            
            # Check display name
            display_name = room_type.replace('_', ' ')
            if display_name.lower() in user_response_lower:
                return room_type
        
        # Keyword matching as fallback
        detection_result = self.detect_room_from_message(user_response)
        if detection_result.confidence >= self.MEDIUM_CONFIDENCE_THRESHOLD:
            return detection_result.room_type
        
        return None
    
    def get_default_room_type(self) -> str:
        """Get default room type when detection fails"""
        return "general"  # Changed from "backyard" to be more neutral