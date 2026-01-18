from PIL import Image, ImageDraw, ImageColor
import numpy as np
from ...api import Template
from ...config import Config
from ..panoramic import PanoramicTemplate

def find_coeffs(source_coords, target_coords):
    """
    Calculate coefficients for perspective transformation.
    """
    matrix = []
    for s, t in zip(source_coords, target_coords):
        matrix.append([t[0], t[1], 1, 0, 0, 0, -s[0]*t[0], -s[0]*t[1]])
        matrix.append([0, 0, 0, t[0], t[1], 1, -s[1]*t[0], -s[1]*t[1]])

    A = np.matrix(matrix, dtype=float)
    B = np.array(source_coords).reshape(8)

    res = np.dot(np.linalg.inv(A.T * A) * A.T, B)
    return np.array(res).reshape(8)

class PerspectiveTemplate(PanoramicTemplate):
    """
    A hybrid template:
    - Index 0-1: Tilted perspective flow with continuous panoramic background.
    - Index 2+: Standard flat layout (with continuous panoramic background).
    """
    
    def process(self, screenshot: Image.Image, text_config: dict, device_frame: Image.Image | None = None, index: int = 0, total: int = 1) -> Image.Image:
        # 1. Config & Colors
        bg_color = text_config.get('background_color', '#F5F5F7')
        
        # 2. Canvas
        canvas = Image.new('RGB', (self.CANVAS_WIDTH, self.CANVAS_HEIGHT), bg_color)
        
        # 3. Draw Panoramic Wave (ALWAYS)
        # Using parent logic
        wave_color = text_config.get('panoramic_color', '#C7C7CC')
        self._draw_panoramic_wave(canvas, wave_color, index, total)

        draw = ImageDraw.Draw(canvas)
        
        # 4. Text (Standard)
        self._draw_text(draw, text_config)
        
        # 5. Device
        
        # Fallback to Standard/Panoramic layout for 3rd screen onwards (Index >= 2)
        # BUT we already drew the background and text on *this* canvas.
        # So we can't just call super().process() because that creates a new canvas.
        # We need to draw the device FLAT here.
        
        if device_frame:
             flat_device = device_frame
        else:
             flat_device = screenshot.resize((1206, 2622), Image.LANCZOS)

        if index >= 2:
            # Standard Upright Layout
            # Center horizontally
            device_x = (self.CANVAS_WIDTH - flat_device.width) // 2
            # Fixed Y offset (check standard template constant)
            # StandardTemplate uses calculated Y based on text, but here we can approximate or recalculate
            # self._draw_text returns nothing currently in previous refactor (it draws in place).
            # The standard layout puts device relative to text bottom.
            # Ideally _draw_text should return the next Y.
            # For now, let's use fixed offset consistent with other templates.
            device_y = self.PHONE_TOP_OFFSET + 250 # Adjust to match Visuals
            
            # Since _draw_text puts text at HEADER_MARGIN, and we want device below.
            # Let's say:
            # Title ~200px + 95pt + gap + Subtitle + gap
            # Standard puts it dynamically.
            # We'll use a fixed visually pleasing position.
            
            canvas.paste(flat_device, (device_x, device_y), flat_device)
            return canvas

        # === Perspective Logic for Index 0, 1 ===
        
        # Geometry: "Standing Phone Receding Right"
        w, h = flat_device.size
        
        # Distortion Parameters
        vertical_shrink = 180
        horizontal_shrink = 100
        
        target_w = w - horizontal_shrink
        
        # Source Points
        src_points = [(0, 0), (w, 0), (w, h), (0, h)]
        
        # Target Points (Trapezoid)
        p_tl = (0, 0)
        p_tr = (target_w, vertical_shrink)
        p_br = (target_w, h - vertical_shrink)
        p_bl = (0, h)
        
        # Center on canvas
        offset_x = (index - 1) * 30
        
        visual_w = target_w
        
        base_x = (self.CANVAS_WIDTH - visual_w) // 2 + offset_x
        base_y = self.PHONE_TOP_OFFSET + 300 # Detailed tuning
        
        # Shadow
        shadow_offset_x = 40
        shadow_offset_y = 60
        
        dst_points = [
            (base_x + p_tl[0], base_y + p_tl[1]),
            (base_x + p_tr[0], base_y + p_tr[1]),
            (base_x + p_br[0], base_y + p_br[1]),
            (base_x + p_bl[0], base_y + p_bl[1])
        ]
        
        dst_points_shadow = [
            (x + shadow_offset_x, y + shadow_offset_y) for x, y in dst_points
        ]
        
        coeffs = find_coeffs(dst_points, src_points)
        coeffs_shadow = find_coeffs(dst_points_shadow, src_points)
        
        # Transform Shadow
        if flat_device.mode == 'RGBA':
            alpha = flat_device.split()[3]
            shadow_source = Image.new('RGBA', flat_device.size, (0, 0, 0, 0))
            shadow_fill = (0, 0, 0, 80)
            shadow_source.paste(shadow_fill, [0, 0, w, h], mask=alpha)
            
            shadow_layer = shadow_source.transform(
                (self.CANVAS_WIDTH, self.CANVAS_HEIGHT),
                Image.PERSPECTIVE,
                coeffs_shadow,
                Image.BICUBIC,
                fillcolor=None
            )
            from PIL import ImageFilter
            shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=20))
            canvas.paste(shadow_layer, (0, 0), shadow_layer)

        # Transform Device
        transformed = flat_device.transform(
            (self.CANVAS_WIDTH, self.CANVAS_HEIGHT),
            Image.PERSPECTIVE,
            coeffs,
            Image.BICUBIC,
            fillcolor=None
        )
        
        canvas.paste(transformed, (0, 0), transformed)
        
        return canvas

