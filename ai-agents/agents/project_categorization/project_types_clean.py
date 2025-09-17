"""
Project Type Mapping - Clean version without synonym mapping
Used by both CIA and IRIS agents for consistent project categorization
LLM handles all intelligence via enum constraint
"""

# 14 Service Categories with their common project types
PROJECT_TYPE_MAPPING = {
    "Installation": [
        # Outdoor & Landscaping Installations (20)
        "turf_installation", "pool_installation", "hot_tub_installation", 
        "fence_installation", "deck_installation", "patio_installation",
        "pergola_installation", "gazebo_installation", "retaining_wall_installation",
        "shed_installation", "playground_installation", "driveway_installation",
        "walkway_installation", "irrigation_system_installation", 
        "outdoor_lighting_installation", "holiday_lighting_installation",
        "outdoor_kitchen_installation", "fire_pit_installation", 
        "greenhouse_installation", "drainage_system_installation",
        
        # Home Systems Installations (20)  
        "hvac_installation", "solar_panel_installation", "generator_installation",
        "water_heater_installation", "water_softener_installation", 
        "sump_pump_installation", "radon_system_installation",
        "security_system_installation", "smart_home_system_installation",
        "ventilation_fan_installation", "ev_charger_installation",
        "central_vacuum_installation", "fire_sprinkler_installation",
        "smoke_detector_installation", "carbon_monoxide_detector_installation",
        "water_filtration_installation", "electrical_panel_installation",
        "backup_battery_system_installation", "home_network_installation",
        "data_cabling_installation",
        
        # Interior Installations (20)
        "flooring_installation", "window_installation", "door_installation",
        "garage_door_installation", "appliance_installation", 
        "cabinet_installation", "countertop_installation", 
        "interior_lighting_installation", "fireplace_installation",
        "trim_molding_installation", "drywall_installation", 
        "insulation_installation", "soundproofing_installation",
        "closet_system_installation", "window_treatment_installation",
        "skylight_installation", "railing_installation", 
        "bathroom_fixture_installation", "kitchen_fixture_installation",
        "glass_shower_enclosure_installation",
        
        # Specialty & Tech Installations (20)
        "home_theater_installation", "home_audio_installation", 
        "projector_installation", "satellite_dish_installation",
        "antenna_installation", "intercom_system_installation",
        "video_doorbell_installation", "smart_lock_installation",
        "camera_system_installation", "sauna_installation",
        "steam_shower_installation", "wine_cellar_installation",
        "lightning_protection_system_installation", 
        "driveway_gate_operator_installation", "access_control_system_installation",
        "storm_shutter_installation", "awning_installation",
        "solar_tube_installation", "waterproofing_system_installation",
        "elevator_or_lift_installation"
    ],
    
    "Renovation": [
        # Interior Renovations (7)
        "kitchen_renovation", "bathroom_renovation", "basement_renovation",
        "attic_renovation", "whole_home_renovation", "garage_conversion",
        "home_addition",
        
        # Exterior & Outdoor Renovations (8)
        "exterior_renovation", "porch_renovation", "deck_renovation",
        "patio_renovation", "sunroom_renovation", "landscaping_renovation",
        "driveway_renovation", "roof_renovation"
    ],
    
    "Repair": [
        # Outdoor & Landscaping Repairs (20)
        "turf_repair", "pool_repair", "hot_tub_repair", 
        "fence_repair", "deck_repair", "patio_repair",
        "pergola_repair", "gazebo_repair", "retaining_wall_repair",
        "shed_repair", "playground_repair", "driveway_repair",
        "walkway_repair", "irrigation_system_repair", 
        "outdoor_lighting_repair", "holiday_lighting_repair",
        "outdoor_kitchen_repair", "fire_pit_repair", 
        "greenhouse_repair", "drainage_system_repair",
        
        # Home Systems Repairs (20)
        "hvac_repair", "solar_panel_repair", "generator_repair",
        "water_heater_repair", "water_softener_repair", 
        "sump_pump_repair", "radon_system_repair",
        "security_system_repair", "smart_home_system_repair",
        "ventilation_fan_repair", "ev_charger_repair",
        "central_vacuum_repair", "fire_sprinkler_repair",
        "smoke_detector_repair", "carbon_monoxide_detector_repair",
        "water_filtration_repair", "electrical_panel_repair",
        "backup_battery_system_repair", "home_network_repair",
        "data_cabling_repair",
        
        # Interior Repairs (20)
        "flooring_repair", "window_repair", "door_repair",
        "garage_door_repair", "appliance_repair", 
        "cabinet_repair", "countertop_repair", 
        "interior_lighting_repair", "fireplace_repair",
        "trim_molding_repair", "drywall_repair", 
        "insulation_repair", "soundproofing_repair",
        "closet_system_repair", "window_treatment_repair",
        "skylight_repair", "railing_repair", 
        "bathroom_fixture_repair", "kitchen_fixture_repair",
        "glass_shower_enclosure_repair",
        
        # Specialty & Tech Repairs (20)
        "home_theater_repair", "home_audio_repair", 
        "projector_repair", "satellite_dish_repair",
        "antenna_repair", "intercom_system_repair",
        "video_doorbell_repair", "smart_lock_repair",
        "camera_system_repair", "sauna_repair",
        "steam_shower_repair", "wine_cellar_repair",
        "lightning_protection_system_repair", 
        "driveway_gate_operator_repair", "access_control_system_repair",
        "storm_shutter_repair", "awning_repair",
        "solar_tube_repair", "waterproofing_system_repair",
        "elevator_or_lift_repair",
        
        # Also keep general repair terms
        "roof_repair", "plumbing_repair", "electrical_repair", 
        "foundation_repair"
    ],
    
    "Replacement": [
        # Outdoor & Landscaping Replacements (20)
        "turf_replacement", "pool_replacement", "hot_tub_replacement", 
        "fence_replacement", "deck_replacement", "patio_replacement",
        "pergola_replacement", "gazebo_replacement", "retaining_wall_replacement",
        "shed_replacement", "playground_replacement", "driveway_replacement",
        "walkway_replacement", "irrigation_system_replacement", 
        "outdoor_lighting_replacement", "holiday_lighting_replacement",
        "outdoor_kitchen_replacement", "fire_pit_replacement", 
        "greenhouse_replacement", "drainage_system_replacement",
        
        # Home Systems Replacements (20)
        "hvac_replacement", "solar_panel_replacement", "generator_replacement",
        "water_heater_replacement", "water_softener_replacement", 
        "sump_pump_replacement", "radon_system_replacement",
        "security_system_replacement", "smart_home_system_replacement",
        "ventilation_fan_replacement", "ev_charger_replacement",
        "central_vacuum_replacement", "fire_sprinkler_replacement",
        "smoke_detector_replacement", "carbon_monoxide_detector_replacement",
        "water_filtration_replacement", "electrical_panel_replacement",
        "backup_battery_system_replacement", "home_network_replacement",
        "data_cabling_replacement",
        
        # Interior Replacements (20)
        "flooring_replacement", "window_replacement", "door_replacement",
        "garage_door_replacement", "appliance_replacement", 
        "cabinet_replacement", "countertop_replacement", 
        "interior_lighting_replacement", "fireplace_replacement",
        "trim_molding_replacement", "drywall_replacement", 
        "insulation_replacement", "soundproofing_replacement",
        "closet_system_replacement", "window_treatment_replacement",
        "skylight_replacement", "railing_replacement", 
        "bathroom_fixture_replacement", "kitchen_fixture_replacement",
        "glass_shower_enclosure_replacement",
        
        # Specialty & Tech Replacements (20)
        "home_theater_replacement", "home_audio_replacement", 
        "projector_replacement", "satellite_dish_replacement",
        "antenna_replacement", "intercom_system_replacement",
        "video_doorbell_replacement", "smart_lock_replacement",
        "camera_system_replacement", "sauna_replacement",
        "steam_shower_replacement", "wine_cellar_replacement",
        "lightning_protection_system_replacement", 
        "driveway_gate_operator_replacement", "access_control_system_replacement",
        "storm_shutter_replacement", "awning_replacement",
        "solar_tube_replacement", "waterproofing_system_replacement",
        "elevator_or_lift_replacement",
        
        # Also keep general replacement terms
        "roof_replacement"
    ],
    
    "Maintenance": [
        # Regular Maintenance Services (30)
        "lawn_maintenance", "pool_maintenance", "hvac_maintenance",
        "gutter_cleaning", "pressure_washing", "window_cleaning",
        "roof_maintenance", "deck_staining", "driveway_sealing",
        "pest_control_maintenance", "septic_maintenance", "chimney_cleaning",
        "air_duct_cleaning", "water_heater_flush", "generator_maintenance",
        "sprinkler_winterization", "tree_trimming", "mulch_installation",
        "fertilizer_application", "weed_control", "snow_removal",
        "holiday_decoration_maintenance", "filter_replacement", "caulking_maintenance",
        "paint_touch_ups", "grout_maintenance", "appliance_maintenance",
        "garage_door_maintenance", "fence_staining", "solar_panel_cleaning"
    ],
    
    "Emergency": [
        # Emergency Response Services (25)
        "emergency_plumbing", "emergency_electrical", "emergency_hvac",
        "emergency_roofing", "flood_damage", "fire_damage",
        "storm_damage", "emergency_tree_removal", "emergency_board_up",
        "burst_pipe", "sewer_backup_cleanup", "mold_remediation",
        "emergency_locksmith", "emergency_glass_repair", "emergency_garage_door",
        "emergency_water_heater", "emergency_generator", "emergency_pest_control",
        "emergency_structural_repair", "emergency_chimney_repair", "emergency_foundation",
        "emergency_septic", "emergency_well_pump", "gas_leak", "power_outage"
    ],
    
    "Ongoing": [
        # Recurring Service Contracts (20)
        "weekly_lawn_care", "biweekly_pool_service", "monthly_pest_control",
        "quarterly_hvac_service", "seasonal_gutter_cleaning", "annual_roof_inspection",
        "monthly_cleaning_service", "weekly_trash_service", "snow_removal_contract",
        "landscaping_service", "home_watch_service", "property_maintenance",
        "security_monitoring", "irrigation_maintenance_contract", "pond_maintenance",
        "fountain_maintenance", "parking_lot_maintenance", "commercial_cleaning",
        "janitorial_services", "grounds_maintenance"
    ],
    
    "Labor Only": [
        # Customer Provides Materials (20)
        "labor_only_flooring", "labor_only_painting", "labor_only_drywall",
        "labor_only_tile", "labor_only_deck", "labor_only_fence",
        "labor_only_landscaping", "labor_only_roofing", "labor_only_siding",
        "labor_only_plumbing", "labor_only_electrical", "labor_only_framing",
        "labor_only_concrete", "labor_only_masonry", "demolition",
        "labor_only_insulation", "labor_only_cabinet_install", "labor_only_countertop",
        "furniture_assembly", "moving_assistance", "excavation", "cleanup", "hauling", "general_labor"
    ],
    
    "Consultation": [
        # Professional Consultation Services (15)
        "design_consultation", "architectural_consultation", "engineering_consultation",
        "landscape_design_consultation", "interior_design_consultation", "color_consultation",
        "energy_audit", "home_inspection", "pool_design_consultation",
        "security_assessment", "accessibility_assessment", "renovation_planning",
        "permit_consultation", "code_consultation", "project_assessment", "contractor_consultation", "estimate", "planning"
    ],
    
    "Events": [
        # One-Time Event Services (15)
        "party_setup", "wedding_setup", "outdoor_event",
        "party_tent_setup", "event_lighting", "temporary_fencing",
        "portable_restroom_rental", "event_landscaping", "holiday_decoration_install",
        "estate_sale_prep", "open_house_staging", "construction_cleanup",
        "move_out_cleaning", "staging", "temporary_installation"
    ],
    
    "Rentals": [
        # Equipment and Service Rentals (15)
        "dumpster_rental", "equipment_rental", "scaffold_rental",
        "portable_storage_rental", "generator_rental", "heater_rental",
        "ac_rental", "fence_panel_rental", "tool_rental", "lift_rental",
        "tent_rental", "portable_toilet_rental", "construction_equipment_rental",
        "party_equipment_rental", "moving_equipment_rental"
    ],
    
    "Lifestyle & Wellness": [
        # Health and Comfort Improvements (20)
        "home_gym", "sauna", "steam_room_installation",
        "meditation_space", "yoga_studio", "wellness_room",
        "air_quality_improvement", "water_quality_system", "hot_tub",
        "soundproofing_project", "spa_installation", "wine_cellar_construction",
        "home_theater_setup", "smart_home_wellness", "ergonomic_home_office",
        "pet_friendly_renovations", "aging_in_place_modifications", "allergy_reduction_improvements",
        "indoor_garden", "zen_garden"
    ],
    
    "Professional/Digital": [
        # Business and Tech Services (15)
        "home_office", "studio_setup", "networking",
        "network_infrastructure", "business_security_system",
        "conference_room_setup", "digital_signage", "pos_system_installation",
        "inventory_system_setup", "commercial_av_system", "data_center_setup",
        "business_automation", "smart_home", "audio_visual", "security_cameras", "automation"
    ],
    
    "AI Solutions": [
        # Smart Home and AI Integration (15)
        "smart_home_ai", "automated_systems", "voice_control",
        "intelligent_lighting", "ai_security", "predictive_maintenance"
    ]
}

# SYNONYM MAPPING REMOVED - LLM handles all intelligence via enum constraint

SCOPE_RULES = {
    "single_trade": [
        # Simple Installation Projects (one contractor type)
        "turf_installation", "fence_installation", "shed_installation", 
        "pergola_installation", "gazebo_installation", "greenhouse_installation",
        "driveway_installation", "walkway_installation", "irrigation_system_installation",
        "outdoor_lighting_installation", "holiday_lighting_installation",
        "outdoor_kitchen_installation", "fire_pit_installation", "drainage_system_installation",
        
        # Single-trade Home Systems
        "hvac_installation", "solar_panel_installation", "generator_installation",
        "water_heater_installation", "water_softener_installation", "sump_pump_installation",
        "security_system_installation", "smart_home_system_installation",
        "ventilation_fan_installation", "ev_charger_installation", "central_vacuum_installation",
        "fire_sprinkler_installation", "smoke_detector_installation", 
        "carbon_monoxide_detector_installation", "water_filtration_installation",
        
        # Single-trade Interior
        "flooring_installation", "window_installation", "door_installation",
        "garage_door_installation", "appliance_installation", "fireplace_installation",
        "trim_molding_installation", "drywall_installation", "insulation_installation",
        "soundproofing_installation", "closet_system_installation", 
        "window_treatment_installation", "skylight_installation", "railing_installation",
        
        # All Repair Projects (typically single contractor)
        "turf_repair", "pool_repair", "hot_tub_repair", "fence_repair", "deck_repair",
        "patio_repair", "pergola_repair", "gazebo_repair", "retaining_wall_repair",
        "shed_repair", "playground_repair", "driveway_repair", "walkway_repair",
        "irrigation_system_repair", "outdoor_lighting_repair", "holiday_lighting_repair",
        "outdoor_kitchen_repair", "fire_pit_repair", "greenhouse_repair", "drainage_system_repair",
        "hvac_repair", "solar_panel_repair", "generator_repair", "water_heater_repair",
        "water_softener_repair", "sump_pump_repair", "radon_system_repair",
        "security_system_repair", "smart_home_system_repair", "ventilation_fan_repair",
        "ev_charger_repair", "central_vacuum_repair", "fire_sprinkler_repair",
        "smoke_detector_repair", "carbon_monoxide_detector_repair", "water_filtration_repair",
        "electrical_panel_repair", "backup_battery_system_repair", "home_network_repair",
        "data_cabling_repair", "flooring_repair", "window_repair", "door_repair",
        "garage_door_repair", "appliance_repair", "cabinet_repair", "countertop_repair",
        "interior_lighting_repair", "fireplace_repair", "trim_molding_repair", "drywall_repair",
        "insulation_repair", "soundproofing_repair", "closet_system_repair",
        "window_treatment_repair", "skylight_repair", "railing_repair", 
        "bathroom_fixture_repair", "kitchen_fixture_repair", "glass_shower_enclosure_repair",
        "roof_repair", "plumbing_repair", "electrical_repair", "foundation_repair",
        
        # All Maintenance (typically single contractor)
        "lawn_maintenance", "pool_maintenance", "hvac_maintenance", "gutter_cleaning",
        "pressure_washing", "window_cleaning", "roof_maintenance", "deck_staining",
        "driveway_sealing", "pest_control_maintenance", "septic_maintenance", 
        "chimney_cleaning", "air_duct_cleaning", "water_heater_flush", "generator_maintenance",
        "sprinkler_winterization", "tree_trimming", "mulch_installation", 
        "fertilizer_application", "weed_control", "snow_removal",
        
        # All Emergency (immediate single contractor response)
        "emergency_plumbing", "emergency_electrical", "emergency_hvac", "emergency_roofing",
        "flood_damage", "fire_damage", "storm_damage", "emergency_tree_removal",
        "emergency_board_up", "burst_pipe", "sewer_backup_cleanup", "mold_remediation",
        "emergency_locksmith", "emergency_glass_repair", "emergency_garage_door",
        "emergency_water_heater", "emergency_generator", "emergency_pest_control",
        "emergency_structural_repair", "emergency_chimney_repair", "emergency_foundation",
        "emergency_septic", "emergency_well_pump", "gas_leak", "power_outage"
    ],
    
    "multi_trade": [
        # Multi-trade Installation projects
        "pool_installation", "hot_tub_installation", "deck_installation", 
        "patio_installation", "retaining_wall_installation", "playground_installation",
        "cabinet_installation", "countertop_installation", "interior_lighting_installation",
        "bathroom_fixture_installation", "kitchen_fixture_installation",
        "glass_shower_enclosure_installation", "home_theater_installation", 
        "home_audio_installation", "projector_installation", "satellite_dish_installation",
        "antenna_installation", "intercom_system_installation", "video_doorbell_installation",
        "smart_lock_installation", "camera_system_installation", "sauna_installation",
        "steam_shower_installation", "wine_cellar_installation",
        
        # Multi-trade Renovation projects
        "kitchen_renovation", "bathroom_renovation", "basement_renovation",
        "attic_renovation", "garage_conversion", "home_addition",
        "porch_renovation", "deck_renovation", "patio_renovation",
        "sunroom_renovation", "landscaping_renovation", "driveway_renovation",
        "roof_renovation"
    ],
    
    "full_renovation": [
        # Full home renovation projects
        "whole_home_renovation", "exterior_renovation"
    ]
}

# Capabilities mapping
CAPABILITIES_MAPPING = {
    # Installation Category Capabilities
    "turf_installation": ["landscaping", "excavation", "drainage"],
    "pool_installation": ["pool_construction", "plumbing", "electrical", "permits", "excavation"],
    "hot_tub_installation": ["plumbing", "electrical", "concrete_work"],
    "fence_installation": ["fencing", "excavation", "permits"],
    "deck_installation": ["carpentry", "permits", "foundation"],
    
    # Renovation Category Capabilities
    "kitchen_renovation": ["plumbing", "electrical", "cabinetry", "countertops", "flooring", "permits"],
    "bathroom_renovation": ["plumbing", "electrical", "tiling", "fixtures", "waterproofing", "permits"],
    "basement_renovation": ["electrical", "plumbing", "insulation", "drywall", "flooring", "permits"],
    "attic_renovation": ["electrical", "insulation", "drywall", "flooring", "ventilation", "permits"],
    "whole_home_renovation": ["general_contractor", "permits", "project_management"],
    "garage_conversion": ["electrical", "plumbing", "insulation", "drywall", "flooring", "permits"],
    "home_addition": ["general_contractor", "foundation", "framing", "permits", "project_management"],
    
    # Repair Category Capabilities  
    "roof_repair": ["roofing", "safety_equipment"],
    "plumbing_repair": ["plumbing", "water_damage_restoration"],
    "electrical_repair": ["electrical", "safety_equipment"],
    "hvac_repair": ["hvac", "refrigeration"],
    
    # Emergency Category Capabilities
    "emergency_plumbing": ["plumbing", "24_hour_availability", "water_damage_restoration"],
    "emergency_electrical": ["electrical", "24_hour_availability", "safety_equipment"],
    "emergency_hvac": ["hvac", "24_hour_availability"],
    "flood_damage": ["water_damage_restoration", "mold_remediation", "emergency_response"],
    "fire_damage": ["fire_damage_restoration", "smoke_damage_restoration", "emergency_response"],
    "storm_damage": ["roofing", "emergency_response", "tree_removal", "board_up"],
}

def get_project_scope(project_type: str) -> str:
    """Determine project scope from project type"""
    for scope, types in SCOPE_RULES.items():
        if project_type in types:
            return scope
    
    # Default inference
    if any(word in project_type for word in ["renovation", "remodel", "addition"]):
        return "multi_trade"
    elif project_type in ["whole_house", "complete", "gut"]:
        return "full_renovation"
    else:
        return "single_trade"

def get_required_capabilities(project_type: str) -> list:
    """Get required capabilities for a project type"""
    return CAPABILITIES_MAPPING.get(project_type, [])

# LLM handles all project type normalization via enum constraint
# No synonym matching needed - OpenAI picks from predefined list