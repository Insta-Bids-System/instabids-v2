"""
Dynamic Open Graph Image Generator for Bid Cards
Creates rich preview images for social media sharing
"""
import base64
import io
import textwrap
from typing import Any

from PIL import Image, ImageDraw, ImageFont


class OGImageGenerator:
    def __init__(self):
        self.width = 1200
        self.height = 630
        self.bg_color = (102, 126, 234)  # Instabids brand color
        self.text_color = (255, 255, 255)
        self.accent_color = (118, 75, 162)

        # Try to load fonts, fallback to default if not available
        try:
            self.title_font = ImageFont.truetype("arial.ttf", 48)
            self.subtitle_font = ImageFont.truetype("arial.ttf", 32)
            self.detail_font = ImageFont.truetype("arial.ttf", 24)
        except:
            # Fallback to default font
            self.title_font = ImageFont.load_default()
            self.subtitle_font = ImageFont.load_default()
            self.detail_font = ImageFont.load_default()

    def generate_bid_card_image(self, bid_card_data: dict[str, Any]) -> str:
        """
        Generate Open Graph image for bid card
        Returns base64 encoded PNG image
        """
        # Create image with gradient background
        image = Image.new("RGB", (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(image)

        # Create gradient background
        self._draw_gradient_background(draw)

        # Add Instabids branding
        self._draw_branding(draw)

        # Add project type and location
        project_type = bid_card_data.get("project_type", "Home Project").replace("_", " ").title()
        location = self._format_location(bid_card_data.get("location", {}))

        # Main title
        title_y = 180
        self._draw_centered_text(draw, project_type, title_y, self.title_font, self.text_color)

        # Location subtitle
        if location:
            subtitle_y = title_y + 70
            self._draw_centered_text(draw, location, subtitle_y, self.subtitle_font, self.text_color, opacity=200)

        # Budget and timeline boxes
        budget = bid_card_data.get("budget_display", "Budget TBD")
        timeline = bid_card_data.get("timeline", "Timeline TBD")

        self._draw_info_boxes(draw, budget, timeline)

        # Add decorative elements
        self._draw_decorative_elements(draw, project_type)

        # Convert to base64
        buffer = io.BytesIO()
        image.save(buffer, format="PNG", quality=95)
        buffer.seek(0)

        return base64.b64encode(buffer.getvalue()).decode()

    def _draw_gradient_background(self, draw):
        """Draw gradient background"""
        for y in range(self.height):
            # Calculate gradient color
            ratio = y / self.height
            r = int(self.bg_color[0] + (self.accent_color[0] - self.bg_color[0]) * ratio)
            g = int(self.bg_color[1] + (self.accent_color[1] - self.bg_color[1]) * ratio)
            b = int(self.bg_color[2] + (self.accent_color[2] - self.bg_color[2]) * ratio)

            draw.line([(0, y), (self.width, y)], fill=(r, g, b))

    def _draw_branding(self, draw):
        """Draw Instabids branding"""
        # Logo area (top left)
        brand_text = "INSTABIDS"
        draw.text((40, 40), brand_text, font=self.detail_font, fill=self.text_color)

        # Tagline (top right)
        tagline = "AI-Powered Contractor Marketplace"
        tagline_bbox = draw.textbbox((0, 0), tagline, font=self.detail_font)
        tagline_width = tagline_bbox[2] - tagline_bbox[0]
        draw.text((self.width - tagline_width - 40, 40), tagline,
                 font=self.detail_font, fill=self.text_color)

    def _draw_centered_text(self, draw, text, y, font, color, opacity=255):
        """Draw centered text with optional opacity"""
        # Handle long text by wrapping
        if len(text) > 30:
            wrapped_lines = textwrap.wrap(text, width=30)
            line_height = 60
            total_height = len(wrapped_lines) * line_height
            start_y = y - (total_height // 2)

            for i, line in enumerate(wrapped_lines):
                line_bbox = draw.textbbox((0, 0), line, font=font)
                line_width = line_bbox[2] - line_bbox[0]
                x = (self.width - line_width) // 2

                if opacity < 255:
                    # Create semi-transparent color
                    temp_color = (*color[:3], opacity) if len(color) == 4 else (*color, opacity)
                    draw.text((x, start_y + i * line_height), line, font=font, fill=temp_color)
                else:
                    draw.text((x, start_y + i * line_height), line, font=font, fill=color)
        else:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2

            if opacity < 255:
                temp_color = (*color[:3], opacity) if len(color) == 4 else (*color, opacity)
                draw.text((x, y), text, font=font, fill=temp_color)
            else:
                draw.text((x, y), text, font=font, fill=color)

    def _draw_info_boxes(self, draw, budget, timeline):
        """Draw budget and timeline info boxes"""
        box_width = 320
        box_height = 120
        box_margin = 40

        # Calculate positions for two boxes side by side
        total_width = (box_width * 2) + box_margin
        start_x = (self.width - total_width) // 2
        box_y = 380

        # Budget box (left)
        budget_x = start_x
        self._draw_info_box(draw, budget_x, box_y, box_width, box_height, "💰 Budget", budget)

        # Timeline box (right)
        timeline_x = start_x + box_width + box_margin
        self._draw_info_box(draw, timeline_x, box_y, box_width, box_height, "⏰ Timeline", timeline)

    def _draw_info_box(self, draw, x, y, width, height, label, value):
        """Draw individual info box"""
        # Box background (semi-transparent white)
        draw.rectangle([x, y, x + width, y + height], fill=(255, 255, 255, 30), outline=(255, 255, 255, 100))

        # Label (top of box)
        label_y = y + 20
        label_bbox = draw.textbbox((0, 0), label, font=self.detail_font)
        label_width = label_bbox[2] - label_bbox[0]
        label_x = x + (width - label_width) // 2
        draw.text((label_x, label_y), label, font=self.detail_font, fill=self.text_color)

        # Value (center of box)
        value_y = y + 60
        # Wrap long values
        if len(value) > 20:
            wrapped_value = textwrap.fill(value, width=20)
            lines = wrapped_value.split("\n")
            line_height = 28
            start_value_y = value_y - (len(lines) * line_height // 2)

            for i, line in enumerate(lines):
                line_bbox = draw.textbbox((0, 0), line, font=self.detail_font)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = x + (width - line_width) // 2
                draw.text((line_x, start_value_y + i * line_height), line,
                         font=self.detail_font, fill=self.text_color)
        else:
            value_bbox = draw.textbbox((0, 0), value, font=self.detail_font)
            value_width = value_bbox[2] - value_bbox[0]
            value_x = x + (width - value_width) // 2
            draw.text((value_x, value_y), value, font=self.detail_font, fill=self.text_color)

    def _draw_decorative_elements(self, draw, project_type):
        """Add decorative elements based on project type"""
        # Add some subtle decorative circles
        circle_color = (255, 255, 255, 20)

        # Top right decorative circles
        draw.ellipse([self.width - 150, 50, self.width - 50, 150], fill=circle_color)
        draw.ellipse([self.width - 100, 100, self.width - 20, 180], fill=circle_color)

        # Bottom left decorative circles
        draw.ellipse([50, self.height - 150, 150, self.height - 50], fill=circle_color)
        draw.ellipse([20, self.height - 180, 100, self.height - 100], fill=circle_color)

        # Project type icon in bottom right
        icon_map = {
            "kitchen": "🏠",
            "bathroom": "🚿",
            "roof": "🏘️",
            "floor": "🪵",
            "paint": "🎨",
            "landscape": "🌿",
            "electrical": "⚡",
            "plumbing": "🔧",
            "hvac": "🌡️"
        }

        # Find matching icon
        icon = "🔨"  # default
        for key, emoji in icon_map.items():
            if key in project_type.lower():
                icon = emoji
                break

        # Draw large icon in bottom right (if font supports it)
        try:
            icon_font = ImageFont.truetype("seguiemj.ttf", 80)  # Emoji font
            draw.text((self.width - 150, self.height - 150), icon,
                     font=icon_font, fill=(255, 255, 255, 100))
        except:
            # Fallback: draw a simple geometric shape
            draw.ellipse([self.width - 140, self.height - 140, self.width - 60, self.height - 60],
                        fill=(255, 255, 255, 50))

    def _format_location(self, location):
        """Format location string"""
        if not location:
            return ""

        city = location.get("city", "")
        state = location.get("state", "")

        if city and state:
            return f"{city}, {state}"
        elif city:
            return city
        elif state:
            return state
        else:
            return ""

    def save_image_to_file(self, base64_image: str, filename: str):
        """Save base64 image to file (for testing)"""
        image_data = base64.b64decode(base64_image)
        with open(filename, "wb") as f:
            f.write(image_data)

# Initialize global generator
og_generator = OGImageGenerator()

def generate_og_image_for_bid_card(bid_card_data: dict[str, Any]) -> str:
    """
    Generate Open Graph image for bid card
    Returns base64 encoded PNG image
    """
    return og_generator.generate_bid_card_image(bid_card_data)
