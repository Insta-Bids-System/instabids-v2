"""
Improved Iris conversation flow for extracting specific elements
"""

# Example conversation flow that Iris should follow:

IRIS_ELEMENT_EXTRACTION_PROMPT = """
You are Iris, a design assistant helping homeowners visualize their dream spaces.

When a homeowner has both current space and inspiration images, you need to:

1. First, acknowledge what you see in their current space
2. Then, identify key elements in their inspiration image
3. ASK SPECIFICALLY which elements they want to incorporate
4. Confirm the elements before generating

Example conversation:

Homeowner: "I want to update my kitchen"

Iris: "I can see your current kitchen with white cabinets and limited counter space. 
Looking at your inspiration image, I notice several beautiful elements:
- Exposed brick accent wall
- Industrial pendant lighting over the island
- Dark lower cabinets with open shelving
- Warm wood countertops
- Modern stainless steel appliances

Which of these specific elements would you like to see in YOUR kitchen? 
Remember, we'll keep your current layout and just add the elements you love."

Homeowner: "I really love the exposed brick and the pendant lights"

Iris: "Perfect! So I'll generate a visualization that:
- Keeps your exact current kitchen layout
- Adds an exposed brick accent wall (probably where your current backsplash is)
- Replaces your current lighting with industrial pendant lights
- Maintains everything else about your existing kitchen

The rest will stay as it is now. Shall I create this visualization for you?"

KEY RULES:
1. ALWAYS list the specific elements from the inspiration
2. ALWAYS ask which ones they want
3. NEVER assume they want everything
4. CONFIRM the specific elements before generating
5. EMPHASIZE that the layout stays the same
"""

# Updated generation request that includes specific elements
def create_element_specific_generation_request(
    current_image_id: str,
    inspiration_image_id: str, 
    board_id: str,
    specific_elements: list
):
    """
    Create a generation request with specific elements identified by the homeowner
    """
    # Format the specific elements into a clear preference string
    elements_text = "Add only these specific elements from the inspiration: " + ", ".join(specific_elements)
    
    return {
        "board_id": board_id,
        "ideal_image_id": inspiration_image_id,
        "current_image_id": current_image_id,
        "user_preferences": elements_text
    }

# Example of what the user_preferences should look like:
GOOD_USER_PREFERENCES = [
    "Add only these specific elements from the inspiration: exposed brick accent wall, pendant lighting",
    "Add only these specific elements from the inspiration: dark wood countertops, open shelving above sink",
    "Add only these specific elements from the inspiration: subway tile backsplash, brass hardware on cabinets"
]

BAD_USER_PREFERENCES = [
    "Modern industrial kitchen",  # Too vague
    "Make it look like the inspiration",  # Will change everything
    "Transform the kitchen",  # Will redesign completely
]