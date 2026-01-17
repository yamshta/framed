from pathlib import Path
from PIL import Image, ImageFont
from .api import Template, Canvas

class StandardTemplate(Template):
    name = "standard"
    
    def render(self, canvas: Canvas, screenshots: List[Image.Image], config: Dict[str, Any]):
        # Config params
        title = config.get('text', {}).get('title', '')
        subtitle = config.get('text', {}).get('subtitle', '')
        font_path = config.get('font', 'Arial.ttf') # fallback needed
        
        # Draw Background
        # (Already filled by Canvas Init if bg_color passed, but specific override here)
        
        # Load Fonts (Simplified)
        try:
            font_title = ImageFont.truetype(font_path, 100)
            font_sub = ImageFont.truetype(font_path, 50)
        except:
            font_title = ImageFont.load_default()
            font_sub = ImageFont.load_default()
            
        # Draw Title
        # Basic centering logic
        w = canvas.width
        canvas.text((100, 200), title, font_title, "#000000")
        canvas.text((100, 350), subtitle, font_sub, "#666666")
        
        # Place Screenshot
        if screenshots:
            shot = screenshots[0]
            # Resize logic omitted for brevity, assuming standard size
            
            # Simple placing
            x = (w - shot.width) // 2
            y = 500
            canvas.place_image(shot, (x, y))
