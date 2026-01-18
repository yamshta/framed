from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from ..standard import StandardTemplate


def find_coeffs(source_coords, target_coords):
    """Calculate coefficients for perspective transformation."""
    matrix = []
    for s, t in zip(source_coords, target_coords):
        matrix.append([t[0], t[1], 1, 0, 0, 0, -s[0]*t[0], -s[0]*t[1]])
        matrix.append([0, 0, 0, t[0], t[1], 1, -s[1]*t[0], -s[1]*t[1]])

    A = np.matrix(matrix, dtype=float)
    B = np.array(source_coords).reshape(8)

    res = np.dot(np.linalg.inv(A.T * A) * A.T, B)
    return np.array(res).reshape(8)


class CascadeTemplate(StandardTemplate):
    """
    A template that composites multiple device frames into a single output image.
    Creates a cascade/fan effect with rotation and overlap.
    """
    
    def process_group(self, device_frames: list[Image.Image], text_configs: list[dict], lang: str) -> Image.Image:
        """
        Process a group of screenshots into a single composite image.
        
        Args:
            device_frames: List of device frames (already composited with bezel).
            text_configs: List of text configurations for each screen.
            lang: Language code for text.
        
        Returns:
            Composite image with all devices arranged in cascade.
        """
        if not device_frames:
            raise ValueError("No device frames provided")
        
        # Use the first screen's config for background
        bg_color = text_configs[0].get('background_color', '#F5F5F7') if text_configs else '#F5F5F7'
        
        # Create canvas
        canvas = Image.new('RGBA', (self.CANVAS_WIDTH, self.CANVAS_HEIGHT), bg_color)
        
        # Cascade Configuration
        num_devices = len(device_frames)
        
        # Reference: First device at FRONT, last at BACK (leftmost)
        # Rotation: ~-15 degrees (clockwise tilt, subtle)
        rotation_angle = -15
        
        # Scale: Devices are scaled down to fit multiple
        base_scale = 0.48 if num_devices >= 3 else 0.55
        
        # Offset configuration: Each device is offset from the previous
        # Horizontal offset (moving right)
        h_offset = 320
        # Vertical offset (moving up)
        v_offset = 100
        
        # Starting position (leftmost, backmost device)
        start_x = 50
        start_y = self.CANVAS_HEIGHT * 0.6
        
        # Draw devices from BACK to FRONT (first in list should be FRONT, so reverse)
        for i, device_frame in enumerate(reversed(device_frames)):
            # Scale
            w, h = device_frame.size
            new_w = int(w * base_scale)
            new_h = int(h * base_scale)
            scaled = device_frame.resize((new_w, new_h), Image.LANCZOS)
            
            # Rotate
            rotated = scaled.rotate(rotation_angle, expand=True, resample=Image.BICUBIC)
            
            # Calculate position
            # i=0 is the LAST device in list (backmost visually)
            # As i increases, we move towards the front (rightward, upward)
            x = start_x + (i * h_offset)
            y = int(start_y - (i * v_offset) - rotated.height)
            
            # Create shadow
            if rotated.mode == 'RGBA':
                alpha = rotated.split()[3]
                shadow = Image.new('RGBA', rotated.size, (0, 0, 0, 0))
                shadow_fill = (0, 0, 0, 60)
                shadow.paste(shadow_fill, [0, 0, rotated.size[0], rotated.size[1]], mask=alpha)
                shadow = shadow.filter(ImageFilter.GaussianBlur(radius=25))
                
                # Paste shadow (offset)
                shadow_offset = 30
                canvas.paste(shadow, (x + shadow_offset, y + shadow_offset), shadow)
            
            # Paste device
            canvas.paste(rotated, (x, y), rotated)
        
        # Draw Text
        # For cascade, we use the FIRST screen's text, positioned top-left
        draw = ImageDraw.Draw(canvas)
        
        if text_configs:
            first_config = text_configs[0]
            title = first_config.get('title_text', '')
            subtitle = first_config.get('subtitle_text', '')
            text_color = first_config.get('text_color', '#1D1D1F')
            subtitle_color = first_config.get('subtitle_color', '#86868B')
            
            title_font = self._load_font(95, bold=True)
            subtitle_font = self._load_font(45, bold=False)
            
            # Left-aligned text
            text_x = 100
            current_y = self.HEADER_MARGIN
            
            if title:
                lines = title.split('\n')
                for line in lines:
                    draw.text((text_x, current_y), line, font=title_font, fill=text_color)
                    bbox = draw.textbbox((0, 0), line, font=title_font)
                    current_y += (bbox[3] - bbox[1]) + self.LINE_SPACING
            
            current_y += (self.CAPTION_SPACING - self.LINE_SPACING)
            
            if subtitle:
                draw.text((text_x, current_y), subtitle, font=subtitle_font, fill=subtitle_color)
        
        # Final Resize
        return canvas.resize(self.APP_STORE_SIZE, Image.Resampling.LANCZOS)
    
    def process(self, screenshot: Image.Image, text_config: dict, device_frame: Image.Image | None = None, index: int = 0, total: int = 1) -> Image.Image:
        """
        Single-device fallback. For cascade, use process_group instead.
        """
        # For single device, just use standard template
        return super().process(screenshot, text_config, device_frame, index, total)
