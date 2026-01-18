from PIL import Image, ImageDraw, ImageColor, ImageFilter
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
    A unified perspective template supporting both:
    1. Group processing (N:1) - "Diagonal Flow" layout (TARIRU style).
    2. Single processing (1:1) - "Standing Phone Receding" layout.
    """
    
    def process_group(self, device_frames: list[Image.Image], text_configs: list[dict], lang: str) -> Image.Image:
        """
        Process multiple device frames into a single composite image using a diagonal layout.
        Mimics the TARIRU "diagonal flow" layout where devices are tilted and cascaded.
        """
        if not device_frames:
            raise ValueError("No device frames provided")
            
        # Use first config for general settings
        base_config = text_configs[0]
        bg_color = base_config.get('background_color', '#F5F5F7')
        
        # Canvas initialization
        canvas = Image.new('RGB', (self.CANVAS_WIDTH, self.CANVAS_HEIGHT), bg_color)
        
        # Draw Background (Wave) - only once
        wave_color = base_config.get('panoramic_color', '#C7C7CC')
        # We use index 0 logic for the group background
        self._draw_panoramic_wave(canvas, wave_color, 0, 1)
        
        draw = ImageDraw.Draw(canvas)
        
        # Draw Text (Title/Subtitle)
        self._draw_text(draw, base_config)
        
        # === Device Layout Logic ===
        # Configuration for "Diagonal Flow"
        # Drawing order: Back (Left) -> Front (Right)
        
        count = len(device_frames)
        
        # TARIRU Layout Settings
        # Rotation: -30 degrees (CCW, Top to Left) or similar.
        # Position: Start from bottom-left area, move up-right.
        
        rotation_angle = -15 # Tilted slightly left
        device_scale = 0.8
        
        # Starting point (Target center of the first device)
        # Assuming 3 devices.
        # We want the group to look centered or intentionally off-center.
        
        start_x = 200
        start_y = 1000
        
        offset_x_step = 250
        offset_y_step = 100 # Move down as we go right? Or up?
        # If we want cascading:
        # Left (Back) -> Right (Front)
        
        for i, device in enumerate(device_frames):
            # 1. Scale
            w, h = device.size
            new_w, new_h = int(w * device_scale), int(h * device_scale)
            scaled = device.resize((new_w, new_h), Image.LANCZOS)
            
            # 2. Rotate
            rotated = scaled.rotate(rotation_angle, resample=Image.BICUBIC, expand=True)
            
            # 3. Position
            # Calculate center position
            pos_x = start_x + (i * offset_x_step)
            pos_y = start_y + (i * offset_y_step)
            
            # Adjust to paste top-left based on center
            img_w, img_h = rotated.size
            paste_x = int(pos_x - (img_w / 2))
            paste_y = int(pos_y - (img_h / 2))
            
            # 4. Shadow
            shadow = Image.new('RGBA', rotated.size, (0,0,0,0))
            alpha = rotated.split()[3]
            shadow.paste((0,0,0,60), (0,0), mask=alpha)
            shadow = shadow.filter(ImageFilter.GaussianBlur(radius=40))
            
            shadow_offset_x = 30
            shadow_offset_y = 50
            
            canvas.paste(shadow, (paste_x + shadow_offset_x, paste_y + shadow_offset_y), shadow)
            
            # 5. Paste Device
            canvas.paste(rotated, (paste_x, paste_y), rotated)
            
        # Resize final output
        final_image = canvas.resize(self.APP_STORE_SIZE, Image.LANCZOS)
        return final_image
    
    def process(self, screenshot: Image.Image, text_config: dict, device_frame: Image.Image | None = None, index: int = 0, total: int = 1) -> Image.Image:
        """
        Single image processing.
        Maintains backward compatibility for the "Standing Phone" 3D perspective layout.
        """
        # 1. Config & Colors
        bg_color = text_config.get('background_color', '#F5F5F7')
        
        # 2. Canvas
        canvas = Image.new('RGB', (self.CANVAS_WIDTH, self.CANVAS_HEIGHT), bg_color)
        
        # 3. Draw Panoramic Wave
        wave_color = text_config.get('panoramic_color', '#C7C7CC')
        self._draw_panoramic_wave(canvas, wave_color, index, total)

        draw = ImageDraw.Draw(canvas)
        
        # 4. Text
        self._draw_text(draw, text_config)
        
        if device_frame:
             flat_device = device_frame
        else:
             flat_device = screenshot.resize((1206, 2622), Image.LANCZOS)

        # 5. Device Layout
        if index >= 2:
            # Standard Upright Layout (for 3rd screen onwards)
            device_x = (self.CANVAS_WIDTH - flat_device.width) // 2
            device_y = self.PHONE_TOP_OFFSET + 250
            canvas.paste(flat_device, (device_x, device_y), flat_device)
            return canvas
        
        # === Perspective Logic for Index 0, 1 ===
        # Geometry: "Standing Phone Receding Right"
        self._apply_perspective_transform(canvas, flat_device, index)
            
        return canvas

    def _apply_perspective_transform(self, canvas, flat_device, index):
        w, h = flat_device.size
        
        # Distortion Parameters
        vertical_shrink = 180
        horizontal_shrink = 100
        target_w = w - horizontal_shrink
        
        src_points = [(0, 0), (w, 0), (w, h), (0, h)]
        
        # Target Points (Trapezoid) for "Receding Right" effect
        p_tl = (0, 0)
        p_tr = (target_w, vertical_shrink)
        p_br = (target_w, h - vertical_shrink)
        p_bl = (0, h)
        
        offset_x = (index - 1) * 30
        visual_w = target_w
        
        base_x = (self.CANVAS_WIDTH - visual_w) // 2 + offset_x
        base_y = self.PHONE_TOP_OFFSET + 300
        
        # Shadow
        shadow_offset_x = 40
        shadow_offset_y = 60
        
        dst_points = [
            (base_x + p_tl[0], base_y + p_tl[1]),
            (base_x + p_tr[0], base_y + p_tr[1]),
            (base_x + p_br[0], base_y + p_br[1]),
            (base_x + p_bl[0], base_y + p_bl[1])
        ]
        
        dst_points_shadow = [(x + shadow_offset_x, y + shadow_offset_y) for x, y in dst_points]
        
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
