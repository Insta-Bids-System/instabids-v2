# Naming Consistency Issues

## Current Inconsistent Patterns:

### Categories 1-4 (Well Developed) - CONSISTENT ✅
- **Installation**: All end with `_installation` 
- **Repair**: All end with `_repair`
- **Replacement**: All end with `_replacement`  
- **Maintenance**: Mixed (some `_maintenance`, some `_cleaning`, some actions like `tree_trimming`)

### Categories 5-14 (Basic Lists) - INCONSISTENT ❌

## Problems Found:

### 5. Renovation
- All end with `_renovation` ✅ CONSISTENT

### 6. Emergency  
- Mixed: `emergency_plumbing` vs `flood_damage` vs `burst_pipe`
- Should be: `emergency_flood`, `emergency_burst_pipe` for consistency?

### 7. Ongoing
- Mixed: `weekly_lawn_care` vs `landscaping_service` vs `snow_removal_contract`
- No consistent pattern (some have frequency, some end with _service, some with _contract)

### 8. Labor Only
- Mostly `labor_only_X` ✅
- But then: `demolition`, `furniture_assembly`, `moving_assistance`, `excavation`, `cleanup`, `hauling`, `general_labor`
- Should be: `labor_only_demolition`, `labor_only_furniture_assembly`, etc?

### 9. Consultation
- Mixed: `design_consultation` vs `energy_audit` vs `home_inspection` vs `estimate` vs `planning`
- Should all end with `_consultation`?

### 10. Events
- Mixed: `party_setup` vs `portable_restroom_rental` vs `construction_cleanup` vs `staging`
- `portable_restroom_rental` belongs in Rentals category!
- No consistent suffix pattern

### 11. Rentals
- Only 8 actually end with `_rental`: `dumpster_rental`, `equipment_rental`, etc.
- Others missing suffix: Should be `tent_rental`, `tool_rental` → already correct
- `portable_toilet_rental` duplicates with Events category's `portable_restroom_rental`

### 12. Lifestyle & Wellness
- Totally mixed: `home_gym` vs `steam_room_installation` vs `meditation_space`
- Some end with `_installation`, others don't
- Should pick one pattern

### 13. Professional/Digital  
- Mixed: `home_office` vs `studio_setup` vs `networking` vs `pos_system_installation`
- Some end with `_setup`, some `_installation`, some nothing

### 14. AI Solutions
- Mixed: `smart_home_ai` vs `automated_systems` vs `voice_control`
- No consistent pattern

## RECOMMENDATION:

Each category should have its own consistent suffix:
1. Installation → `_installation`
2. Repair → `_repair`  
3. Replacement → `_replacement`
4. Maintenance → `_maintenance` or `_service`
5. Renovation → `_renovation`
6. Emergency → `emergency_` prefix
7. Ongoing → `_contract` or `_service`
8. Labor Only → `labor_only_` prefix
9. Consultation → `_consultation`
10. Events → `_event` or `_setup`
11. Rentals → `_rental`
12. Lifestyle & Wellness → `_wellness` or keep mixed?
13. Professional/Digital → `_setup` or `_installation`
14. AI Solutions → `_ai` or `ai_` prefix

This would make the LLM's job MUCH easier - it could learn the pattern!