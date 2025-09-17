"""
Fix the categorization tool to force LLM to pick from pre-loaded project types
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))

from project_categorization.project_types import PROJECT_TYPE_MAPPING

def generate_complete_project_type_enum():
    """Generate the complete enum list of all 449 project types"""
    
    all_types = []
    for category, types in PROJECT_TYPE_MAPPING.items():
        all_types.extend(types)
    
    print("=" * 80)
    print(f"GENERATING COMPLETE PROJECT TYPE ENUM ({len(all_types)} types)")
    print("=" * 80)
    
    # Create the enum array for the tool
    enum_list = '[\n'
    for i, project_type in enumerate(sorted(all_types)):
        if i % 5 == 0 and i > 0:
            enum_list += '\n'
        enum_list += f'                    "{project_type}",'
        if (i + 1) % 5 != 0:
            enum_list += ' '
        else:
            enum_list += '\n'
    
    enum_list += '\n                ]'
    
    print("FIXED CATEGORIZATION TOOL:")
    print("-" * 40)
    
    fixed_tool = f'''CATEGORIZATION_TOOL = {{
    "type": "function",
    "function": {{
        "name": "categorize_project",
        "description": "Categorize a home improvement project - MUST pick from pre-defined project types",
        "parameters": {{
            "type": "object",
            "properties": {{
                "service_category": {{
                    "type": "string",
                    "enum": [
                        "Installation", "Repair", "Replacement", "Renovation", 
                        "Maintenance", "Ongoing", "Emergency", "Labor Only",
                        "Consultation", "Events", "Rentals", 
                        "Lifestyle & Wellness", "Professional/Digital", "AI Solutions"
                    ],
                    "description": "The primary type of service being requested"
                }},
                "normalized_project_type": {{
                    "type": "string",
                    "enum": {enum_list},
                    "description": "MUST pick from the pre-defined project types - no custom types allowed"
                }},
                "project_scope": {{
                    "type": "string", 
                    "enum": ["single_trade", "multi_trade", "full_renovation"],
                    "description": "The complexity/scope level of the project"
                }},
                "confidence_score": {{
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Confidence level in the categorization (0.0 to 1.0)"
                }}
            }},
            "required": ["service_category", "normalized_project_type", "project_scope", "confidence_score"]
        }}
    }}
}}'''
    
    print(fixed_tool)
    
    print("\n" + "=" * 80)
    print("WHAT THIS FIXES:")
    print("=" * 80)
    print("BEFORE (BROKEN):")
    print('  User: "fake grass repair"')
    print('  LLM: "grass_stuff_repair" <- RANDOM!')
    print()
    print("AFTER (FIXED):")  
    print('  User: "fake grass repair"')
    print('  LLM: Must pick from: ["turf_repair", "lawn_maintenance", etc.]')
    print('  LLM: "turf_repair" <- FROM OUR LIST!')
    
    print(f"\nTotal project types in enum: {len(all_types)}")
    
    # Verify no duplicates
    unique_types = set(all_types)
    if len(unique_types) != len(all_types):
        print(f"WARNING: Found {len(all_types) - len(unique_types)} duplicate project types!")
        
        # Find duplicates
        from collections import Counter
        counts = Counter(all_types)
        duplicates = [item for item, count in counts.items() if count > 1]
        print(f"Duplicates: {duplicates}")
    else:
        print("✅ No duplicate project types found")
    
    return fixed_tool

if __name__ == "__main__":
    generate_complete_project_type_enum()