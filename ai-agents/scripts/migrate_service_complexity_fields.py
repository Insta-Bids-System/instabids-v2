#!/usr/bin/env python3
"""
Service Complexity Migration Script
Adds service complexity classification fields to existing bid cards
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_simple import get_supabase_client

# Service complexity classification rules based on project types and trades
SERVICE_COMPLEXITY_MAPPING = {
    # Single-trade services (Group bidding eligible)
    "single-trade": {
        "project_types": [
            "lawn_care", "lawn_maintenance", "landscaping", "turf_installation", "artificial_turf",
            "pool_cleaning", "pool_maintenance", "pool_repair",
            "roofing", "roof_repair", "roof_replacement", "gutter_cleaning", "gutter_installation",
            "tree_removal", "tree_trimming", "tree_service",
            "pressure_washing", "exterior_cleaning",
            "fence_installation", "fence_repair",
            "driveway_repair", "concrete_work", "patio_installation",
            "window_cleaning", "window_repair", "window_replacement",
            "painting_exterior", "painting_interior", "house_painting",
            "hvac_maintenance", "hvac_repair", "air_conditioning",
            "plumbing_repair", "drain_cleaning", "plumbing_maintenance",
            "electrical_repair", "electrical_maintenance"
        ],
        "primary_trades": {
            "lawn_care": "landscaping",
            "lawn_maintenance": "landscaping", 
            "landscaping": "landscaping",
            "turf_installation": "landscaping",
            "artificial_turf": "landscaping",
            "pool_cleaning": "pool_maintenance",
            "pool_maintenance": "pool_maintenance",
            "pool_repair": "pool_maintenance",
            "roofing": "roofing",
            "roof_repair": "roofing",
            "roof_replacement": "roofing",
            "gutter_cleaning": "roofing",
            "gutter_installation": "roofing",
            "tree_removal": "tree_service",
            "tree_trimming": "tree_service",
            "tree_service": "tree_service",
            "pressure_washing": "cleaning",
            "exterior_cleaning": "cleaning",
            "fence_installation": "fencing",
            "fence_repair": "fencing",
            "driveway_repair": "concrete",
            "concrete_work": "concrete",
            "patio_installation": "concrete",
            "window_cleaning": "cleaning",
            "window_repair": "glazing",
            "window_replacement": "glazing",
            "painting_exterior": "painting",
            "painting_interior": "painting", 
            "house_painting": "painting",
            "hvac_maintenance": "hvac",
            "hvac_repair": "hvac",
            "air_conditioning": "hvac",
            "plumbing_repair": "plumbing",
            "drain_cleaning": "plumbing",
            "plumbing_maintenance": "plumbing",
            "electrical_repair": "electrical",
            "electrical_maintenance": "electrical"
        }
    },
    
    # Multi-trade services (Coordinated bidding)
    "multi-trade": {
        "project_types": [
            "kitchen_remodel", "kitchen_renovation", "kitchen_design",
            "bathroom_remodel", "bathroom_renovation", "bathroom_design",
            "basement_finishing", "basement_remodel",
            "room_addition", "home_addition",
            "deck_construction", "deck_installation", "outdoor_living",
            "master_suite_addition", "bedroom_addition",
            "garage_conversion", "attic_conversion",
            "sunroom_addition", "porch_construction",
            "flooring_installation", "hardwood_flooring", "tile_installation"
        ],
        "trade_combinations": {
            "kitchen_remodel": ["plumbing", "electrical", "cabinets", "countertops", "flooring"],
            "kitchen_renovation": ["plumbing", "electrical", "cabinets", "countertops"],
            "bathroom_remodel": ["plumbing", "electrical", "tile", "fixtures"],
            "bathroom_renovation": ["plumbing", "electrical", "tile"],
            "basement_finishing": ["framing", "electrical", "insulation", "drywall", "flooring"],
            "room_addition": ["foundation", "framing", "electrical", "plumbing", "hvac"],
            "deck_construction": ["framing", "concrete", "railing", "staining"],
            "flooring_installation": ["flooring", "trim", "preparation"]
        }
    },
    
    # Complex coordination projects (Not eligible for group bidding)
    "complex-coordination": {
        "project_types": [
            "whole_house_renovation", "house_renovation", "home_renovation",
            "new_construction", "custom_home", "home_building",
            "commercial_buildout", "office_renovation", "retail_buildout",
            "multi_unit_development", "apartment_renovation",
            "major_structural_repair", "foundation_repair_major",
            "second_story_addition", "major_addition"
        ]
    }
}

def classify_project_complexity(project_type: str, description: str = "") -> Tuple[str, int, str, List[str]]:
    """
    Classify a project's service complexity based on project type and description.
    
    Returns:
        Tuple of (service_complexity, trade_count, primary_trade, secondary_trades)
    """
    project_type_lower = project_type.lower().replace(" ", "_").replace("-", "_")
    description_lower = description.lower() if description else ""
    
    # Check for single-trade classification
    single_trade_types = SERVICE_COMPLEXITY_MAPPING["single-trade"]["project_types"]
    primary_trade_map = SERVICE_COMPLEXITY_MAPPING["single-trade"]["primary_trades"]
    
    if project_type_lower in single_trade_types:
        primary_trade = primary_trade_map.get(project_type_lower, project_type_lower)
        return ("single-trade", 1, primary_trade, [])
    
    # Check for multi-trade classification
    multi_trade_types = SERVICE_COMPLEXITY_MAPPING["multi-trade"]["project_types"]
    trade_combinations = SERVICE_COMPLEXITY_MAPPING["multi-trade"]["trade_combinations"]
    
    if project_type_lower in multi_trade_types:
        secondary_trades = trade_combinations.get(project_type_lower, ["general_construction"])
        primary_trade = secondary_trades[0] if secondary_trades else "general_construction"
        remaining_trades = secondary_trades[1:] if len(secondary_trades) > 1 else []
        trade_count = len(secondary_trades) if secondary_trades else 2
        return ("multi-trade", trade_count, primary_trade, remaining_trades)
    
    # Check for complex coordination projects
    complex_types = SERVICE_COMPLEXITY_MAPPING["complex-coordination"]["project_types"]
    if project_type_lower in complex_types:
        return ("complex-coordination", 6, "general_construction", ["electrical", "plumbing", "hvac", "framing", "finishing"])
    
    # Default classification based on description analysis
    if any(keyword in description_lower for keyword in ["kitchen", "bathroom", "remodel", "renovation"]):
        if "kitchen" in description_lower:
            return ("multi-trade", 4, "plumbing", ["electrical", "cabinets", "countertops"])
        elif "bathroom" in description_lower:
            return ("multi-trade", 3, "plumbing", ["electrical", "tile"])
        else:
            return ("multi-trade", 3, "general_construction", ["electrical", "plumbing"])
    
    # Check for single-trade keywords in description
    single_trade_keywords = {
        "lawn": ("single-trade", 1, "landscaping", []),
        "pool": ("single-trade", 1, "pool_maintenance", []),
        "roof": ("single-trade", 1, "roofing", []),
        "tree": ("single-trade", 1, "tree_service", []),
        "paint": ("single-trade", 1, "painting", []),
        "fence": ("single-trade", 1, "fencing", []),
        "concrete": ("single-trade", 1, "concrete", []),
        "window": ("single-trade", 1, "glazing", []),
        "cleaning": ("single-trade", 1, "cleaning", [])
    }
    
    for keyword, classification in single_trade_keywords.items():
        if keyword in description_lower:
            return classification
    
    # Default to single-trade if uncertain
    return ("single-trade", 1, "general", [])

def determine_group_bid_eligibility(service_complexity: str, trade_count: int, primary_trade: str) -> bool:
    """Determine if a project is eligible for group bidding."""
    if service_complexity != "single-trade":
        return False
    
    # Group bidding is primarily for recurring services and standardized work
    group_eligible_trades = [
        "landscaping", "lawn_care", "pool_maintenance", "cleaning", 
        "roofing", "tree_service", "painting", "concrete", "fencing"
    ]
    
    return primary_trade in group_eligible_trades

def migrate_bid_card_complexity():
    """Main migration function to add service complexity fields to existing bid cards."""
    try:
        print("🚀 Starting Service Complexity Migration")
        print("=" * 60)
        
        # Get Supabase client
        supabase = get_supabase_client()
        print("✅ Connected to Supabase")
        
        # Fetch all existing bid cards
        print("\n📋 Fetching existing bid cards...")
        response = supabase.table('bid_cards').select('*').execute()
        bid_cards = response.data
        
        print(f"📊 Found {len(bid_cards)} bid cards to migrate")
        
        if not bid_cards:
            print("ℹ️  No bid cards found. Migration complete.")
            return
        
        # Statistics tracking
        stats = {
            "total_processed": 0,
            "single_trade": 0,
            "multi_trade": 0,
            "complex_coordination": 0,
            "group_eligible": 0,
            "errors": 0
        }
        
        print("\n🔄 Processing bid cards...")
        
        for i, bid_card in enumerate(bid_cards, 1):
            try:
                # Skip if already has service_complexity
                if bid_card.get('service_complexity'):
                    print(f"⏭️  [{i}/{len(bid_cards)}] Skipping {bid_card['bid_card_number']} - already classified")
                    continue
                
                # Classify the project
                service_complexity, trade_count, primary_trade, secondary_trades = classify_project_complexity(
                    bid_card.get('project_type', ''),
                    bid_card.get('description', '')
                )
                
                # Determine group bid eligibility
                group_bid_eligible = determine_group_bid_eligibility(service_complexity, trade_count, primary_trade)
                
                # Prepare update data
                update_data = {
                    'service_complexity': service_complexity,
                    'trade_count': trade_count,
                    'primary_trade': primary_trade,
                    'secondary_trades': secondary_trades,
                    'group_bid_eligible': group_bid_eligible,
                    'updated_at': datetime.utcnow().isoformat()
                }
                
                # Update the bid card
                update_response = supabase.table('bid_cards').update(update_data).eq('id', bid_card['id']).execute()
                
                if update_response.data:
                    # Update statistics
                    stats["total_processed"] += 1
                    stats[service_complexity.replace("-", "_")] += 1
                    if group_bid_eligible:
                        stats["group_eligible"] += 1
                    
                    complexity_emoji = "🔵" if service_complexity == "single-trade" else "🟠" if service_complexity == "multi-trade" else "🔴"
                    group_emoji = "🏘️" if group_bid_eligible else ""
                    
                    print(f"✅ [{i}/{len(bid_cards)}] {complexity_emoji} {bid_card['bid_card_number']}: {service_complexity} - {primary_trade} ({trade_count} trades) {group_emoji}")
                    
                else:
                    print(f"❌ [{i}/{len(bid_cards)}] Failed to update {bid_card['bid_card_number']}")
                    stats["errors"] += 1
                    
            except Exception as e:
                print(f"❌ [{i}/{len(bid_cards)}] Error processing {bid_card.get('bid_card_number', 'Unknown')}: {str(e)}")
                stats["errors"] += 1
        
        # Print final statistics
        print("\n" + "=" * 60)
        print("📊 MIGRATION COMPLETE - SUMMARY STATISTICS")
        print("=" * 60)
        print(f"📝 Total bid cards processed: {stats['total_processed']}")
        print(f"🔵 Single-trade projects: {stats['single_trade']}")
        print(f"🟠 Multi-trade projects: {stats['multi_trade']}")  
        print(f"🔴 Complex coordination projects: {stats['complex_coordination']}")
        print(f"🏘️ Group bidding eligible: {stats['group_eligible']}")
        
        if stats["errors"] > 0:
            print(f"❌ Errors encountered: {stats['errors']}")
        
        print(f"\n💾 Updated {stats['total_processed']} bid cards with service complexity classification")
        print("✨ Service complexity migration completed successfully!")
        
        # Also migrate potential_bid_cards if they exist
        print("\n🔄 Checking potential_bid_cards table...")
        
        try:
            potential_response = supabase.table('potential_bid_cards').select('*').limit(1).execute()
            if potential_response.data:
                migrate_potential_bid_cards()
        except Exception as e:
            print(f"ℹ️  potential_bid_cards table not found or empty: {str(e)}")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        sys.exit(1)

def migrate_potential_bid_cards():
    """Migrate potential_bid_cards table as well."""
    try:
        print("\n🔄 Migrating potential_bid_cards...")
        
        supabase = get_supabase_client()
        response = supabase.table('potential_bid_cards').select('*').execute()
        potential_cards = response.data
        
        if not potential_cards:
            print("ℹ️  No potential bid cards found")
            return
        
        print(f"📋 Found {len(potential_cards)} potential bid cards")
        
        processed = 0
        for card in potential_cards:
            try:
                # Skip if already classified
                if card.get('service_complexity'):
                    continue
                
                # Classify the project
                service_complexity, trade_count, primary_trade, secondary_trades = classify_project_complexity(
                    card.get('project_type', ''),
                    card.get('description', '')
                )
                
                group_bid_eligible = determine_group_bid_eligibility(service_complexity, trade_count, primary_trade)
                
                # Update data
                update_data = {
                    'service_complexity': service_complexity,
                    'trade_count': trade_count,
                    'primary_trade': primary_trade,
                    'secondary_trades': secondary_trades,
                    'group_bid_eligible': group_bid_eligible,
                    'updated_at': datetime.utcnow().isoformat()
                }
                
                # Update the potential bid card
                supabase.table('potential_bid_cards').update(update_data).eq('id', card['id']).execute()
                processed += 1
                
            except Exception as e:
                print(f"❌ Error updating potential bid card {card.get('id')}: {str(e)}")
        
        print(f"✅ Updated {processed} potential bid cards")
        
    except Exception as e:
        print(f"❌ Error migrating potential_bid_cards: {str(e)}")

def preview_migration():
    """Preview what the migration would do without making changes."""
    print("🔍 PREVIEW MODE - Service Complexity Migration")
    print("=" * 60)
    
    try:
        supabase = get_supabase_client()
        response = supabase.table('bid_cards').select('id, bid_card_number, project_type, description, service_complexity').limit(10).execute()
        bid_cards = response.data
        
        print(f"📋 Previewing first {len(bid_cards)} bid cards:")
        print()
        
        for card in bid_cards:
            if card.get('service_complexity'):
                print(f"⏭️  {card['bid_card_number']}: Already classified as {card['service_complexity']}")
                continue
            
            service_complexity, trade_count, primary_trade, secondary_trades = classify_project_complexity(
                card.get('project_type', ''),
                card.get('description', '')
            )
            
            group_eligible = determine_group_bid_eligibility(service_complexity, trade_count, primary_trade)
            
            complexity_emoji = "🔵" if service_complexity == "single-trade" else "🟠" if service_complexity == "multi-trade" else "🔴"
            group_emoji = "🏘️" if group_eligible else ""
            
            print(f"{complexity_emoji} {card['bid_card_number']}")
            print(f"   Project: {card.get('project_type', 'N/A')}")
            print(f"   → Complexity: {service_complexity}")
            print(f"   → Primary Trade: {primary_trade}")
            print(f"   → Trade Count: {trade_count}")
            print(f"   → Secondary Trades: {secondary_trades}")
            print(f"   → Group Eligible: {'Yes' if group_eligible else 'No'} {group_emoji}")
            print()
        
        print("💡 Run with --execute to perform the actual migration")
        
    except Exception as e:
        print(f"❌ Preview failed: {str(e)}")

if __name__ == "__main__":
    print("🏗️  InstaBids Service Complexity Migration Tool")
    print("=" * 60)
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--preview":
        preview_migration()
    elif len(sys.argv) > 1 and sys.argv[1] == "--execute":
        migrate_bid_card_complexity()
    else:
        print("Usage:")
        print("  python migrate_service_complexity_fields.py --preview   # Preview changes")
        print("  python migrate_service_complexity_fields.py --execute   # Execute migration")
        print()
        print("This script will add service complexity classification fields to existing bid cards:")
        print("  • service_complexity (single-trade/multi-trade/complex-coordination)")
        print("  • trade_count (number of trades required)")
        print("  • primary_trade (main trade category)")
        print("  • secondary_trades (additional trades needed)")
        print("  • group_bid_eligible (eligible for group bidding)")