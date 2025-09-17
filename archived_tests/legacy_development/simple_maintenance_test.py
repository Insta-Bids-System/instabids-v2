#!/usr/bin/env python3
"""
Simple test to demonstrate how maintenance issues are extracted from REAL photos
This shows the direct database query without the API layer
"""

# Direct database query simulation based on the Supabase results we got
real_maintenance_data = [
    {
        "original_filename": "WhatsApp-Living-Room-Broken-Blinds.jpg",
        "detected_issues": ["broken blinds"],  # Simple string format
        "created_at": "2025-08-12 00:45:20"
    },
    {
        "original_filename": "roof_maintenance_test.jpg", 
        "detected_issues": [
            {
                "description": "Missing roof shingles near chimney area",
                "severity": "urgent",
                "type": "repair", 
                "confidence": 0.95,
                "estimated_cost": "high"
            },
            {
                "description": "Gutters clogged with debris and leaves",
                "severity": "medium",
                "type": "maintenance",
                "confidence": 0.87, 
                "estimated_cost": "low"
            }
        ],
        "created_at": "2025-08-12 16:25:32"
    }
]

def extract_maintenance_issues_from_photos():
    """Extract maintenance issues from real photo AI analysis data"""
    
    print("=== HOW THE REAL 'NEEDS REPAIR' SYSTEM WORKS ===")
    print()
    
    maintenance_issues = []
    
    for photo in real_maintenance_data:
        detected_issues = photo["detected_issues"]
        
        print(f"PHOTO: {photo['original_filename']}")
        print(f"   Uploaded: {photo['created_at']}")
        print(f"   AI Detected: {len(detected_issues)} issue(s)")
        print()
        
        # Handle both old and new formats (exactly like the backend does)
        for issue in detected_issues:
            if isinstance(issue, str):
                # Old format: simple string
                maintenance_issues.append({
                    "id": f"photo-{len(maintenance_issues)}",
                    "photo_filename": photo["original_filename"],
                    "description": issue,
                    "severity": "medium",  # Default for real detected issues
                    "type": "maintenance",
                    "confidence": 0.8,     # Default confidence for real AI
                    "estimated_cost": "medium",
                    "detected_at": photo["created_at"]
                })
                print(f"   Issue: {issue} (simple format)")
                
            elif isinstance(issue, dict):
                # New format: detailed object
                maintenance_issues.append({
                    "id": f"photo-{len(maintenance_issues)}",
                    "photo_filename": photo["original_filename"], 
                    "description": issue["description"],
                    "severity": issue["severity"],
                    "type": issue["type"],
                    "confidence": issue["confidence"],
                    "estimated_cost": issue["estimated_cost"],
                    "detected_at": photo["created_at"]
                })
                print(f"   URGENT Issue: {issue['description']}")
                print(f"      Severity: {issue['severity']} | Cost: {issue['estimated_cost']} | Confidence: {int(issue['confidence']*100)}%")
        print()
    
    print("=== EXTRACTED MAINTENANCE ISSUES FOR 'NEEDS REPAIR' DASHBOARD ===")
    print()
    
    for i, issue in enumerate(maintenance_issues, 1):
        print(f"REPAIR #{i}:")
        print(f"  From Photo: {issue['photo_filename']}")
        print(f"  Description: {issue['description']}")
        print(f"  Severity: {issue['severity']}")
        print(f"  Type: {issue['type']}")
        print(f"  Cost: {issue['estimated_cost']}")
        print(f"  AI Confidence: {int(issue['confidence']*100)}%")
        print(f"  Detected: {issue['detected_at']}")
        print()
    
    print("KEY POINT: This data comes from:")
    print("   1. User uploads property photos")
    print("   2. GPT-4o Vision API analyzes each photo")
    print("   3. AI detects maintenance issues and stores in database")
    print("   4. 'Needs Repair' dashboard extracts and displays them")
    print("   5. User can select issues and create bid cards for contractors")
    
    return maintenance_issues

if __name__ == "__main__":
    issues = extract_maintenance_issues_from_photos()
    print(f"\nTOTAL: {len(issues)} maintenance issues ready for bid card creation")