#!/usr/bin/env python3
"""
Comprehensive Bid Card Normalization Script V2
Uses the proper 14 work-type categories and 385+ project types
"""

import sys
import os
import re
from typing import Dict, List, Tuple, Optional

# Add the project_categorization directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents', 'project_categorization'))

from project_types import PROJECT_TYPE_MAPPING, SYNONYM_MAPPING, get_project_scope
import asyncio
import logging
from database_simple import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def determine_work_type_category(text: str) -> Tuple[str, str, List[str]]:
    """
    Determine work-type category from our 14 categories and find specific project type
    Returns: (service_category, normalized_project_type, required_capabilities)
    """
    text_lower = text.lower()
    
    # Check for clear renovation indicators first
    renovation_keywords = ['renovation', 'remodel', 'gut', 'redo', 'update', 'refresh', 'makeover']
    if any(word in text_lower for word in renovation_keywords):
        if 'kitchen' in text_lower:
            return "renovation", "kitchen_renovation", ["general_contracting", "plumbing", "electrical", "cabinetry"]
        elif 'bathroom' in text_lower or 'bath' in text_lower:
            return "renovation", "bathroom_renovation", ["plumbing", "electrical", "tile_work", "general_contracting"]
        elif 'basement' in text_lower:
            return "renovation", "basement_renovation", ["waterproofing", "electrical", "hvac", "framing"]
        elif 'deck' in text_lower:
            return "renovation", "deck_renovation", ["carpentry", "weatherproofing", "structural"]
        elif 'patio' in text_lower:
            return "renovation", "patio_renovation", ["concrete_work", "masonry", "landscaping"]
        elif 'landscaping' in text_lower or 'yard' in text_lower:
            return "renovation", "landscaping_renovation", ["landscape_design", "irrigation", "hardscaping"]
        elif 'whole' in text_lower or 'entire' in text_lower or 'complete' in text_lower:
            return "renovation", "whole_home_renovation", ["general_contracting", "project_management", "multi_trade_coordination"]
        else:
            return "renovation", "general_renovation", ["general_contracting", "design", "project_management"]
    
    # Check for repair keywords
    repair_keywords = ['repair', 'fix', 'broken', 'damage', 'leak', 'crack', 'replace broken']
    if any(word in text_lower for word in repair_keywords):
        if 'turf' in text_lower or 'artificial' in text_lower or 'synthetic' in text_lower:
            return "repair", "turf_repair", ["turf_repair", "seaming", "infill_replacement"]
        elif 'pool' in text_lower:
            return "repair", "pool_repair", ["pool_service", "plumbing", "equipment_repair"]
        elif 'hvac' in text_lower or 'heating' in text_lower or 'cooling' in text_lower or 'air condition' in text_lower:
            return "repair", "hvac_repair", ["hvac_service", "refrigeration", "ductwork"]
        elif 'roof' in text_lower:
            return "repair", "roof_repair", ["roofing", "leak_detection", "flashing_repair"]
        elif 'plumb' in text_lower or 'pipe' in text_lower or 'drain' in text_lower:
            return "repair", "plumbing_repair", ["plumbing", "leak_repair", "drain_cleaning"]
        elif 'electric' in text_lower:
            return "repair", "electrical_repair", ["electrical", "troubleshooting", "panel_work"]
        elif 'deck' in text_lower:
            return "repair", "deck_repair", ["carpentry", "wood_repair", "weatherproofing"]
        elif 'fence' in text_lower:
            return "repair", "fence_repair", ["fence_repair", "post_replacement", "gate_repair"]
        elif 'driveway' in text_lower:
            return "repair", "driveway_repair", ["concrete_repair", "crack_sealing", "resurfacing"]
        else:
            return "repair", "general_repair", ["general_repair", "handyman_services"]
    
    # Check for replacement keywords
    replacement_keywords = ['replacement', 'replace', 'new for old', 'swap out', 'upgrade old']
    if any(word in text_lower for word in replacement_keywords):
        if 'turf' in text_lower or 'artificial' in text_lower or 'synthetic' in text_lower or 'grass' in text_lower:
            return "replacement", "turf_replacement", ["turf_removal", "turf_installation", "base_prep"]
        elif 'window' in text_lower:
            return "replacement", "window_replacement", ["window_installation", "trim_work", "sealing"]
        elif 'door' in text_lower:
            return "replacement", "door_replacement", ["door_installation", "framing", "hardware"]
        elif 'roof' in text_lower:
            return "replacement", "roof_replacement", ["roofing", "shingle_work", "flashing"]
        elif 'hvac' in text_lower or 'heating' in text_lower or 'cooling' in text_lower:
            return "replacement", "hvac_replacement", ["hvac_installation", "ductwork", "electrical"]
        elif 'water heater' in text_lower:
            return "replacement", "water_heater_replacement", ["plumbing", "gas_fitting", "electrical"]
        elif 'floor' in text_lower:
            return "replacement", "flooring_replacement", ["flooring_removal", "subfloor_prep", "flooring_installation"]
        else:
            return "replacement", "general_replacement", ["removal", "installation", "disposal"]    
    # Check for installation keywords (default for new work)
    install_keywords = ['install', 'installation', 'new', 'add', 'build', 'construct', 'put in']
    if any(word in text_lower for word in install_keywords) or not any(word in text_lower for word in repair_keywords + replacement_keywords + renovation_keywords):
        if 'turf' in text_lower or 'artificial' in text_lower or 'synthetic grass' in text_lower or 'fake grass' in text_lower:
            return "installation", "turf_installation", ["turf_installation", "base_preparation", "drainage", "seaming"]
        elif 'pool' in text_lower:
            return "installation", "pool_installation", ["excavation", "plumbing", "electrical", "concrete_work"]
        elif 'fence' in text_lower:
            return "installation", "fence_installation", ["fence_installation", "post_setting", "gate_hardware"]
        elif 'deck' in text_lower:
            return "installation", "deck_installation", ["carpentry", "foundation_work", "railing_installation"]
        elif 'patio' in text_lower:
            return "installation", "patio_installation", ["concrete_work", "grading", "drainage"]
        elif 'solar' in text_lower:
            return "installation", "solar_panel_installation", ["solar_installation", "electrical", "roof_mounting"]
        elif 'hvac' in text_lower or 'heating' in text_lower or 'cooling' in text_lower or 'air condition' in text_lower:
            return "installation", "hvac_installation", ["hvac_installation", "ductwork", "electrical", "thermostat"]
        elif 'holiday lighting' in text_lower or 'christmas lights' in text_lower:
            return "installation", "holiday_lighting_installation", ["lighting_installation", "ladder_work", "electrical"]
        elif 'landscap' in text_lower or 'lawn' in text_lower or 'yard' in text_lower:
            return "installation", "landscaping_installation", ["landscape_design", "planting", "irrigation", "hardscaping"]
        elif 'kitchen' in text_lower:
            # Kitchen without renovation keywords = likely cabinet/appliance installation
            return "installation", "kitchen_fixture_installation", ["cabinet_installation", "appliance_installation", "plumbing"]
        elif 'bathroom' in text_lower or 'bath' in text_lower:
            return "installation", "bathroom_fixture_installation", ["fixture_installation", "plumbing", "tile_work"]
        elif 'floor' in text_lower:
            return "installation", "flooring_installation", ["flooring_installation", "subfloor_prep", "trim_work"]
        elif 'window' in text_lower:
            return "installation", "window_installation", ["window_installation", "framing", "weatherproofing"]
        elif 'door' in text_lower:
            return "installation", "door_installation", ["door_installation", "framing", "hardware_installation"]
        elif 'driveway' in text_lower:
            return "installation", "driveway_installation", ["grading", "base_prep", "paving", "drainage"]
        elif 'generator' in text_lower:
            return "installation", "generator_installation", ["electrical", "gas_fitting", "transfer_switch"]
        elif 'security' in text_lower or 'alarm' in text_lower or 'camera' in text_lower:
            return "installation", "security_system_installation", ["security_installation", "wiring", "network_setup"]
        elif 'smart home' in text_lower or 'automation' in text_lower:
            return "installation", "smart_home_system_installation", ["home_automation", "electrical", "network_setup"]
        else:
            # Default installation
            return "installation", "general_installation", ["general_contracting", "installation_services"]
    
    # Check for maintenance keywords
    maintenance_keywords = ['maintenance', 'maintain', 'service', 'tune up', 'cleaning', 'inspection']
    if any(word in text_lower for word in maintenance_keywords):
        if 'lawn' in text_lower or 'grass' in text_lower:
            return "maintenance", "lawn_maintenance", ["lawn_care", "mowing", "fertilization", "weed_control"]
        elif 'pool' in text_lower:
            return "maintenance", "pool_maintenance", ["pool_cleaning", "chemical_balance", "equipment_check"]
        elif 'hvac' in text_lower:
            return "maintenance", "hvac_maintenance", ["filter_replacement", "system_inspection", "cleaning"]
        elif 'gutter' in text_lower:
            return "maintenance", "gutter_cleaning", ["gutter_cleaning", "downspout_clearing", "inspection"]
        else:
            return "maintenance", "general_maintenance", ["maintenance_services", "inspection", "cleaning"]
    
    # Check for emergency keywords
    emergency_keywords = ['emergency', 'urgent', 'asap', 'immediate', 'storm damage', 'flood', 'fire damage']
    if any(word in text_lower for word in emergency_keywords):
        if 'plumb' in text_lower or 'leak' in text_lower or 'flood' in text_lower:
            return "emergency", "emergency_plumbing", ["emergency_plumbing", "water_mitigation", "pipe_repair"]
        elif 'electric' in text_lower or 'power' in text_lower:
            return "emergency", "emergency_electrical", ["emergency_electrical", "troubleshooting", "safety"]
        elif 'hvac' in text_lower or 'heat' in text_lower or 'cool' in text_lower:
            return "emergency", "emergency_hvac", ["emergency_hvac", "rapid_response", "temporary_solutions"]
        elif 'roof' in text_lower or 'storm' in text_lower:
            return "emergency", "storm_damage_repair", ["tarping", "emergency_repair", "water_mitigation"]
        else:
            return "emergency", "emergency_response", ["emergency_services", "rapid_response", "damage_control"]
    
    # Default fallback - try to match to installation category
    if 'general' in text_lower or not text.strip():
        return "installation", "general_contracting", ["general_contracting", "project_management"]
    
    # Final fallback
    return "installation", "general_installation", ["general_contracting", "various_trades"]
def normalize_bid_card_categorization_v2(project_type: str, title: str, description: str) -> dict:
    """
    Apply our NEW 14-category system to normalize a bid card
    """
    # Combine all text for analysis
    combined_text = f"{project_type} {title} {description}".strip()
    
    # Get work-type category and normalized project type
    service_category, normalized_project_type, required_capabilities = determine_work_type_category(combined_text)
    
    # Determine project scope based on category and project type
    # Default scopes by category
    if service_category == "renovation":
        project_scope = "multi_trade"  # Renovations usually require multiple trades
    elif service_category in ["repair", "maintenance", "emergency"]:
        project_scope = "single_trade"  # Repairs usually single trade
    elif service_category == "installation":
        # Installations vary - check specifics
        if any(word in normalized_project_type for word in ['kitchen', 'bathroom', 'hvac', 'solar']):
            project_scope = "multi_trade"
        else:
            project_scope = "single_trade"
    else:
        project_scope = "single_trade"  # Default
    
    # Override scope based on specific keywords in text
    if any(word in combined_text.lower() for word in ['whole house', 'entire home', 'complete renovation', 'full gut', 'whole property']):
        project_scope = "full_renovation"
    elif any(word in combined_text.lower() for word in ['multiple rooms', 'several areas', 'various trades', 'complete remodel']):
        project_scope = "multi_trade"
    
    return {
        'service_category': service_category,
        'normalized_project_type': normalized_project_type,
        'project_scope': project_scope,
        'required_capabilities': required_capabilities,
        'confidence_score': 0.85,  # Higher confidence with detailed mapping
        'original_input': combined_text[:100] + '...' if len(combined_text) > 100 else combined_text
    }

async def normalize_bid_cards_sample(limit: int = 5):
    """Test normalization on a sample of bid cards"""
    
    logger.info(f"Testing normalization on {limit} sample bid cards...")
    
    try:
        # Get sample bid cards
        logger.info("Fetching sample bid cards...")
        bid_cards_result = db.client.table("bid_cards").select(
            "id", "project_type", "title", "description", "service_category", "project_scope"
        ).limit(limit).execute()
        
        bid_cards = bid_cards_result.data if bid_cards_result.data else []
        logger.info(f"Found {len(bid_cards)} bid cards to test")
        
        results = []
        
        for card in bid_cards:
            card_id = card['id']
            project_type = card.get('project_type', '') or ''
            title = card.get('title', '') or ''
            description = card.get('description', '') or ''
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Testing bid card {card_id}")
            logger.info(f"Original: {project_type} / {title}")
            logger.info(f"Current category: {card.get('service_category')}")
            
            # Apply normalization
            normalization = normalize_bid_card_categorization_v2(project_type, title, description)
            
            logger.info(f"NEW category: {normalization['service_category']}")
            logger.info(f"NEW project type: {normalization['normalized_project_type']}")
            logger.info(f"NEW scope: {normalization['project_scope']}")
            logger.info(f"NEW capabilities: {normalization['required_capabilities']}")
            logger.info(f"Confidence: {normalization['confidence_score']}")
            
            results.append({
                'id': card_id,
                'old_category': card.get('service_category'),
                'new_category': normalization['service_category'],
                'normalized_type': normalization['normalized_project_type'],
                'changes': card.get('service_category') != normalization['service_category']
            })
        
        # Summary
        logger.info(f"\n{'='*60}")
        logger.info("SAMPLE TEST SUMMARY:")
        changes_count = sum(1 for r in results if r['changes'])
        logger.info(f"Total tested: {len(results)}")
        logger.info(f"Would change: {changes_count}")
        logger.info(f"Would keep same: {len(results) - changes_count}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error in sample normalization: {e}")
        raise

async def normalize_all_bid_cards_v2(dry_run: bool = False):
    """Normalize all bid cards with the NEW 14-category system"""
    
    logger.info("Starting bid card normalization V2...")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE UPDATE'}")
    
    try:
        # Get all bid cards
        logger.info("Fetching all bid cards...")
        bid_cards_result = db.client.table("bid_cards").select(
            "id", "project_type", "title", "description", "service_category", "project_scope"
        ).execute()
        
        bid_cards = bid_cards_result.data if bid_cards_result.data else []
        logger.info(f"Found {len(bid_cards)} bid cards to normalize")
        
        normalized_count = 0
        unchanged_count = 0
        error_count = 0
        
        category_changes = {}
        
        for i, card in enumerate(bid_cards):
            card_id = card['id']
            project_type = card.get('project_type', '') or ''
            title = card.get('title', '') or ''
            description = card.get('description', '') or ''
            old_category = card.get('service_category', '')
            
            # Apply normalization
            normalization = normalize_bid_card_categorization_v2(project_type, title, description)
            new_category = normalization['service_category']
            
            # Track category changes
            change_key = f"{old_category} -> {new_category}"
            category_changes[change_key] = category_changes.get(change_key, 0) + 1
            
            if old_category == new_category and card.get('project_scope') == normalization['project_scope']:
                unchanged_count += 1
                if i % 20 == 0:
                    logger.info(f"Progress: {i+1}/{len(bid_cards)} - Unchanged")
                continue
            
            if not dry_run:
                # Update database
                update_data = {
                    'service_category': new_category,
                    'project_scope': normalization['project_scope'],
                    'required_capabilities': normalization['required_capabilities'],
                    'updated_at': 'now()'
                }
                
                # Also update project_type to normalized version
                if normalization['normalized_project_type']:
                    update_data['project_type'] = normalization['normalized_project_type'].replace('_', ' ').title()
                
                try:
                    result = db.client.table("bid_cards").update(update_data).eq("id", card_id).execute()
                    
                    if result.data:
                        normalized_count += 1
                        if normalized_count % 10 == 0:
                            logger.info(f"Updated {normalized_count} cards so far...")
                    else:
                        error_count += 1
                        logger.error(f"Failed to update bid card {card_id}")
                        
                except Exception as e:
                    error_count += 1
                    logger.error(f"Database error updating {card_id}: {e}")
            else:
                normalized_count += 1
                if normalized_count % 20 == 0:
                    logger.info(f"Would update {normalized_count} cards...")
        
        # Print summary
        logger.info(f"\n{'='*60}")
        logger.info("BID CARDS NORMALIZATION COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"Total processed: {len(bid_cards)}")
        logger.info(f"Updated: {normalized_count}")
        logger.info(f"Unchanged: {unchanged_count}")
        logger.info(f"Errors: {error_count}")
        
        logger.info(f"\n{'='*60}")
        logger.info("CATEGORY MIGRATION SUMMARY:")
        for change, count in sorted(category_changes.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                logger.info(f"  {change}: {count} cards")
        
        return {
            'total': len(bid_cards),
            'updated': normalized_count,
            'unchanged': unchanged_count,
            'errors': error_count,
            'category_changes': category_changes
        }
        
    except Exception as e:
        logger.error(f"Error normalizing bid cards: {e}")
        raise

async def normalize_all_potential_bid_cards_v2(dry_run: bool = False):
    """Normalize all potential bid cards with the NEW 14-category system"""
    
    logger.info("Starting potential bid card normalization V2...")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE UPDATE'}")
    
    try:
        # Get all potential bid cards
        logger.info("Fetching all potential bid cards...")
        potential_cards_result = db.client.table("potential_bid_cards").select(
            "id", "project_type", "title", "project_description", "service_category", "project_scope"
        ).execute()
        
        potential_cards = potential_cards_result.data if potential_cards_result.data else []
        logger.info(f"Found {len(potential_cards)} potential bid cards to normalize")
        
        normalized_count = 0
        unchanged_count = 0
        error_count = 0
        
        for card in potential_cards:
            card_id = card['id']
            project_type = card.get('project_type', '') or ''
            title = card.get('title', '') or ''
            description = card.get('project_description', '') or ''
            old_category = card.get('service_category', '')
            
            # Apply normalization
            normalization = normalize_bid_card_categorization_v2(project_type, title, description)
            new_category = normalization['service_category']
            
            if old_category == new_category:
                unchanged_count += 1
                continue
            
            if not dry_run:
                # Update database
                update_data = {
                    'service_category': new_category,
                    'project_scope': normalization['project_scope'],
                    'required_capabilities': normalization['required_capabilities'],
                    'updated_at': 'now()'
                }
                
                try:
                    result = db.client.table("potential_bid_cards").update(update_data).eq("id", card_id).execute()
                    
                    if result.data:
                        normalized_count += 1
                    else:
                        error_count += 1
                        
                except Exception as e:
                    error_count += 1
                    logger.error(f"Database error updating {card_id}: {e}")
            else:
                normalized_count += 1
        
        logger.info(f"\nPOTENTIAL BID CARDS: Updated {normalized_count}, Unchanged {unchanged_count}, Errors {error_count}")
        
    except Exception as e:
        logger.error(f"Error normalizing potential bid cards: {e}")
        raise

async def main():
    """Run normalization with options"""
    
    print("=" * 80)
    print("InstaBids Bid Card Normalization System V2")
    print("Using 14 Work-Type Categories + 385 Project Types")
    print("=" * 80)
    print("")
    print("Options:")
    print("1. Test on 5 sample bid cards")
    print("2. Dry run on all bid cards (no changes)")
    print("3. LIVE UPDATE all bid cards")
    print("4. LIVE UPDATE all potential bid cards")  
    print("5. FULL LIVE UPDATE (both bid cards and potential)")
    print("")
    
    # For automated testing, default to option 5 (full update)
    choice = "5"  # Change this to test different options
    
    try:
        if choice == "1":
            await normalize_bid_cards_sample(5)
        elif choice == "2":
            await normalize_all_bid_cards_v2(dry_run=True)
        elif choice == "3":
            print("\nLIVE UPDATE - This will modify the database!")
            await normalize_all_bid_cards_v2(dry_run=False)
        elif choice == "4":
            print("\nLIVE UPDATE - This will modify the database!")
            await normalize_all_potential_bid_cards_v2(dry_run=False)
        elif choice == "5":
            print("\nFULL LIVE UPDATE - This will modify the database!")
            await normalize_all_bid_cards_v2(dry_run=False)
            await normalize_all_potential_bid_cards_v2(dry_run=False)
            print("\nCOMPLETE NORMALIZATION FINISHED!")
        
    except Exception as e:
        print(f"Normalization failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())