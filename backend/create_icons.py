"""
Create simple placeholder icons for testing
"""
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("PIL not installed. Installing pillow...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
    from PIL import Image, ImageDraw, ImageFont

import os

# Create icons directory if it doesn't exist
icons_dir = "../extension/icons"
os.makedirs(icons_dir, exist_ok=True)

def create_icon(size, filename):
    # Create image with orange background
    img = Image.new('RGB', (size, size), color='#FF9800')
    
    # Draw circle
    draw = ImageDraw.Draw(img)
    margin = size // 8
    draw.ellipse([margin, margin, size-margin, size-margin], fill='#FFC107')
    
    # Try to add text
    try:
        # Use a larger font size for visibility
        font_size = size // 2
        font = ImageFont.truetype("arial.ttf", font_size)
        text = "??"
    except:
        # Fallback if emoji font not available
        font_size = size // 3
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        text = "S"
    
    # Get text size and position
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((size - text_width) // 2, (size - text_height) // 2 - bbox[1])
    
    # Draw text
    draw.text(position, text, fill='#000000', font=font)
    
    # Save
    filepath = os.path.join(icons_dir, filename)
    img.save(filepath)
    print(f"? Created {filepath}")

# Create all three sizes
print("Creating placeholder icons...")
create_icon(16, "icon16.png")
create_icon(48, "icon48.png")
create_icon(128, "icon128.png")

print("\n? All icons created!")
print(f"Location: {os.path.abspath(icons_dir)}")
