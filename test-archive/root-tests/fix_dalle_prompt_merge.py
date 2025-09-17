#!/usr/bin/env python3
"""
Fix the DALL-E prompt to properly merge images instead of creating split-screen
"""

# Find and update the generate_dalle_prompt function
import os

file_path = "Documents/instabids/ai-agents/api/image_generation.py"

# Read the current file
with open(file_path, "r") as f:
    content = f.read()

# Create improved prompt generation
better_prompt = '''def generate_dalle_prompt(ideal_analysis: dict, current_analysis: dict, user_preferences: str = None, custom_prompt: str = None) -> str:
    """
    Generate an optimized DALL-E prompt that merges current space with inspiration features
    """
    if custom_prompt:
        return custom_prompt
    
    # Extract key elements from analyses
    ideal_style = ideal_analysis.get('style', '')
    ideal_features = ideal_analysis.get('key_features', [])
    ideal_materials = ideal_analysis.get('materials', [])
    current_layout = current_analysis.get('description', 'existing kitchen layout')
    
    # For kitchen transformations, create a merger prompt
    prompt_parts = [
        "Interior kitchen design photograph, photorealistic high-quality rendering.",
        f"Starting with: {current_layout}.",
        f"Transform into: {ideal_style} style kitchen.",
        "IMPORTANT: This is a SINGLE transformed kitchen image, NOT a before/after comparison.",
        "Merge the current kitchen layout with these new design elements:",
    ]
    
    # Add specific transformation elements
    if ideal_features:
        prompt_parts.append(f"Add these features: {', '.join(ideal_features)}.")
    
    if ideal_materials:
        prompt_parts.append(f"Use these materials: {', '.join(ideal_materials)}.")
    
    # Add user preferences
    if user_preferences:
        prompt_parts.append(f"Additional requirements: {user_preferences}")
    
    # Quality specifications
    prompt_parts.extend([
        "Single cohesive kitchen design showing the transformation complete.",
        "Professional architectural photography style.",
        "Natural lighting, high detail, realistic textures.",
        "Wide angle view showing the full transformed kitchen space."
    ])
    
    return " ".join(prompt_parts)'''

# Find the function and replace it
import re

# Pattern to find the function
pattern = r'def generate_dalle_prompt\(.*?\):\s*"""[\s\S]*?"""[\s\S]*?return " ".join\(prompt_parts\)'

# Check if we can find it
if re.search(pattern, content, re.DOTALL):
    print("Found generate_dalle_prompt function")
    # Replace with better version
    content = re.sub(pattern, better_prompt, content, count=1, flags=re.DOTALL)
    
    # Write back
    with open(file_path, "w") as f:
        f.write(content)
    
    print("SUCCESS: Updated DALL-E prompt generation")
    print("\nThe new prompt will:")
    print("- Create a SINGLE transformed kitchen image")
    print("- Merge current layout with inspiration features")
    print("- NOT create a split-screen comparison")
    print("\nNOTE: Server needs restart to use the new prompt")
else:
    print("ERROR: Could not find the generate_dalle_prompt function")
    print("Manual update needed")