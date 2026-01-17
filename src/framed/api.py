from typing import Any, Dict, List, Tuple
from PIL import Image, ImageDraw

class Canvas:
    """Wrapper around PIL Image to provide simplified drawing API"""
    def __init__(self, width: int, height: int, bg_color: str = "#FFFFFF"):
        self.image = Image.new('RGB', (width, height), bg_color)
        self.draw = ImageDraw.Draw(self.image)
        self.width = width
        self.height = height

    def fill(self, color: str):
        self.draw.rectangle((0, 0, self.width, self.height), fill=color)

    def place_image(self, img: Image.Image, pos: Tuple[int, int]):
        self.image.paste(img, pos, img if img.mode == 'RGBA' else None)

    def text(self, xy: Tuple[int, int], text: str, font: Any, fill: str):
        self.draw.text(xy, text, font=font, fill=fill)
        
    def save(self, path: str):
        self.image.save(path)

class Template:
    """Base class for all layout templates"""
    name: str = "base"
    
    def render(self, canvas: Canvas, screenshots: List[Image.Image], config: Dict[str, Any]):
        raise NotImplementedError
