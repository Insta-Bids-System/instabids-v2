# Complete Category Review & Naming Fix Plan

## Category-by-Category Review

### 5. RENOVATION (15 items) 
**Current Naming**: ✅ CONSISTENT - all end with `_renovation`
**Current Items**: 
```
kitchen_renovation, bathroom_renovation, basement_renovation,
attic_renovation, whole_home_renovation, garage_conversion, home_addition,
exterior_renovation, porch_renovation, deck_renovation,
patio_renovation, sunroom_renovation, landscaping_renovation,
driveway_renovation, roof_renovation
```
**ISSUES**: 
- `garage_conversion` should be `garage_renovation`
- `home_addition` should be `addition_renovation`
**MISSING**: bedroom_renovation, office_renovation, laundry_room_renovation, etc.

### 6. EMERGENCY (25 items)
**Current Naming**: ❌ INCONSISTENT 
**Pattern Should Be**: `emergency_` prefix for all
**Current Items Need Fixing**:
```
CORRECT: emergency_plumbing, emergency_electrical, emergency_hvac, etc.
WRONG: flood_damage → emergency_flood
       fire_damage → emergency_fire  
       storm_damage → emergency_storm
       burst_pipe → emergency_burst_pipe
       sewer_backup_cleanup → emergency_sewer_backup
       mold_remediation → emergency_mold
       gas_leak → emergency_gas_leak
       power_outage → emergency_power_outage
```

### 7. ONGOING (20 items)
**Current Naming**: ❌ VERY INCONSISTENT
**Pattern Should Be**: `ongoing_` prefix + service type
**Current Items Need Major Fixing**:
```
weekly_lawn_care → ongoing_lawn_care
biweekly_pool_service → ongoing_pool_service  
monthly_pest_control → ongoing_pest_control
quarterly_hvac_service → ongoing_hvac_service
seasonal_gutter_cleaning → ongoing_gutter_cleaning
annual_roof_inspection → ongoing_roof_inspection
monthly_cleaning_service → ongoing_cleaning_service
weekly_trash_service → ongoing_trash_service
snow_removal_contract → ongoing_snow_removal
landscaping_service → ongoing_landscaping
home_watch_service → ongoing_home_watch
property_maintenance → ongoing_property_maintenance
security_monitoring → ongoing_security_monitoring
irrigation_maintenance_contract → ongoing_irrigation_maintenance
pond_maintenance → ongoing_pond_maintenance
fountain_maintenance → ongoing_fountain_maintenance
parking_lot_maintenance → ongoing_parking_lot_maintenance
commercial_cleaning → ongoing_commercial_cleaning
janitorial_services → ongoing_janitorial
grounds_maintenance → ongoing_grounds_maintenance
```

### 8. LABOR ONLY (24 items)
**Current Naming**: ❌ PARTIALLY INCONSISTENT
**Pattern Should Be**: `labor_only_` prefix for all
**Items Need Fixing**:
```
CORRECT: labor_only_flooring, labor_only_painting, etc.
WRONG: demolition → labor_only_demolition
       furniture_assembly → labor_only_furniture_assembly
       moving_assistance → labor_only_moving
       excavation → labor_only_excavation
       cleanup → labor_only_cleanup
       hauling → labor_only_hauling
       general_labor → labor_only_general
```

### 9. CONSULTATION (18 items)
**Current Naming**: ❌ INCONSISTENT
**Pattern Should Be**: All end with `_consultation`
**Items Need Fixing**:
```
CORRECT: design_consultation, architectural_consultation, etc.
WRONG: energy_audit → energy_consultation
       home_inspection → inspection_consultation
       renovation_planning → renovation_consultation
       estimate → estimate_consultation
       planning → planning_consultation
```

### 10. EVENTS (15 items)
**Current Naming**: ❌ INCONSISTENT
**Pattern Should Be**: All end with `_event`
**Items Need Fixing**:
```
party_setup → party_event
wedding_setup → wedding_event
outdoor_event → outdoor_event ✅
party_tent_setup → tent_event
event_lighting → lighting_event
temporary_fencing → fencing_event
portable_restroom_rental → REMOVE (duplicate with Rentals)
event_landscaping → landscaping_event
holiday_decoration_install → holiday_decoration_event
estate_sale_prep → estate_sale_event
open_house_staging → open_house_event
construction_cleanup → construction_cleanup_event
move_out_cleaning → move_out_event
staging → staging_event
temporary_installation → temporary_installation_event
```

### 11. RENTALS (15 items)
**Current Naming**: ✅ MOSTLY CONSISTENT
**Pattern**: All end with `_rental`
**All Correct**: All 15 items already end with `_rental`

### 12. LIFESTYLE & WELLNESS (20 items)
**Current Naming**: ❌ VERY INCONSISTENT
**Pattern Should Be**: All end with `_wellness`
**Items Need Fixing**:
```
home_gym → home_gym_wellness
sauna → sauna_wellness
steam_room_installation → steam_room_wellness
meditation_space → meditation_wellness
yoga_studio → yoga_wellness
wellness_room → wellness_room ✅
air_quality_improvement → air_quality_wellness
water_quality_system → water_quality_wellness
hot_tub → hot_tub_wellness
soundproofing_project → soundproofing_wellness
spa_installation → spa_wellness
wine_cellar_construction → wine_cellar_wellness
home_theater_setup → home_theater_wellness
smart_home_wellness → smart_home_wellness ✅
ergonomic_home_office → ergonomic_office_wellness
pet_friendly_renovations → pet_friendly_wellness
aging_in_place_modifications → aging_in_place_wellness
allergy_reduction_improvements → allergy_reduction_wellness
indoor_garden → indoor_garden_wellness
zen_garden → zen_garden_wellness
```

### 13. PROFESSIONAL/DIGITAL (16 items)
**Current Naming**: ❌ INCONSISTENT
**Pattern Should Be**: All end with `_professional`
**Items Need Fixing**:
```
home_office → home_office_professional
studio_setup → studio_professional
networking → networking_professional
network_infrastructure → network_infrastructure_professional
business_security_system → security_professional
conference_room_setup → conference_room_professional
digital_signage → digital_signage_professional
pos_system_installation → pos_system_professional
inventory_system_setup → inventory_professional
commercial_av_system → av_system_professional
data_center_setup → data_center_professional
business_automation → automation_professional
smart_home → smart_home_professional
audio_visual → audio_visual_professional
security_cameras → security_cameras_professional
automation → automation_professional (duplicate?)
```

### 14. AI SOLUTIONS (6 items) 
**Current Naming**: ❌ INCONSISTENT  
**Pattern Should Be**: All start with `ai_`
**Items Need Fixing**:
```
smart_home_ai → ai_smart_home
automated_systems → ai_automated_systems
voice_control → ai_voice_control
intelligent_lighting → ai_intelligent_lighting
ai_security → ai_security ✅
predictive_maintenance → ai_predictive_maintenance
```

## Summary of Changes Needed:
1. **Renovation**: Fix 2 items
2. **Emergency**: Fix 8 items  
3. **Ongoing**: Fix ALL 20 items
4. **Labor Only**: Fix 7 items
5. **Consultation**: Fix 5 items
6. **Events**: Fix 14 items, remove 1
7. **Rentals**: ✅ Already good
8. **Lifestyle & Wellness**: Fix 18 items
9. **Professional/Digital**: Fix ALL 16 items
10. **AI Solutions**: Fix 5 items

Total: ~95 items need renaming for consistency!