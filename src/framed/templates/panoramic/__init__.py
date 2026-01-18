from PIL import Image, ImageDraw, ImageFont
import math
from PIL import ImageColor
from ..standard import StandardTemplate

class PanoramicTemplate(StandardTemplate):
    """
    Extends StandardTemplate to add a continuous panoramic wave background
    across multiple screenshots.
    """
    
    def process(self, screenshot: Image.Image, text_config: dict, device_frame: Image.Image | None = None, index: int = 0, total: int = 1) -> Image.Image:
        # Configuration
        bg_color = text_config.get('background_color', '#F5F5F7')
        
        # Create canvas
        canvas = Image.new('RGB', (self.CANVAS_WIDTH, self.CANVAS_HEIGHT), bg_color)
        
        # === Draw Panoramic Background ===
        # Default to enabled, but check config just in case
        wave_color = text_config.get('panoramic_color', '#C7C7CC')
        self._draw_panoramic_wave(canvas, wave_color, index, total)
        
        # === Delegate Rest to Parent ===
        # We want to reuse text and device drawing, but StandardTemplate.process creates a NEW canvas.
        # So we cannot just super().process() easily if we want to draw on OUR canvas.
        # Alternatively, we can let StandardTemplate handle everything and we just hook in?
        # No, StandardTemplate.process creates the canvas.
        
        # Strategy: Re-implement process but reuse helper methods if any.
        # Since StandardTemplate logic is simple, we will duplicate the high-level flow 
        # but inject the wave drawing.
        
        draw = ImageDraw.Draw(canvas)
        
        # Texts
        title = text_config.get('title_text', "")
        subtitle = text_config.get('subtitle_text', "")
        
        # Fonts
        title_font = self._load_font(95, bold=True)
        subtitle_font = self._load_font(45, bold=False)
        
        # Draw Text
        current_y = self.HEADER_MARGIN
        
        # Title
        text_color = text_config.get('text_color', '#1D1D1F')
        if title:
            lines = title.split('\n')
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=title_font)
                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]
                draw.text(((self.CANVAS_WIDTH - w) / 2, current_y), line, font=title_font, fill=text_color)
                current_y += h + self.LINE_SPACING
                
        current_y += (self.CAPTION_SPACING - self.LINE_SPACING)
        
        # Subtitle
        subtitle_color = text_config.get('subtitle_color', '#86868B')
        bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        w = bbox[2] - bbox[0]
        draw.text(((self.CANVAS_WIDTH - w) / 2, current_y), subtitle, font=subtitle_font, fill=subtitle_color)
        
        # Device Frame
        if device_frame:
            # Calculate position
            device_y = current_y + self.PHONE_TOP_OFFSET
            
            # Check if it fits
            remaining_height = self.CANVAS_HEIGHT - device_y
            if device_frame.height > remaining_height:
                # Need to scale down
                scale = remaining_height / device_frame.height
                new_size = (int(device_frame.width * scale), int(device_frame.height * scale))
                device_frame = device_frame.resize(new_size, Image.Resampling.LANCZOS)
            
            # Center horizontally
            device_x = (self.CANVAS_WIDTH - device_frame.width) // 2
            
            # Paste (using mask for transparency)
            canvas.paste(device_frame, (device_x, int(device_y)), device_frame)
            
        # Final Resize
        return canvas.resize(self.APP_STORE_SIZE, Image.Resampling.LANCZOS)

    def _draw_panoramic_wave(self, canvas, wave_color, index, total_screens):
        """
        Draws a multi-layered 'voice-like' waveform across the background using LINES.
        Calculates global coordinates based on index and width to ensure continuity.
        The wave amplitude tapers to a single point at both ends of the panorama.
        """
        draw = ImageDraw.Draw(canvas, 'RGBA')
        width, height = canvas.size
        
        # Wave Configuration
        base_y = height * 0.70
        global_offset = index * width
        total_width = total_screens * width  # Total panoramic width
        
        # Parse color
        try:
            rgb = ImageColor.getrgb(wave_color)
        except:
            rgb = (199, 199, 204)  # Default #C7C7CC
        
        # Define layers: (amplitude, freq_mult, phase, opacity, stroke_width)
        layers = [
            (350, 0.8, 0, 0.2, 16),      # Thick, faint background
            (250, 1.5, 2.0, 0.4, 10),    # Medium defined wave
            (180, 2.2, 4.0, 0.7, 6),     # Main sharp voice line
            (100, 3.0, 6.0, 0.5, 4),     # Accent line
        ]
        
        for amplitude, freq_mult, phase, opacity, stroke_width in layers:
            rgba_color = rgb + (int(opacity * 255),)
            points = []
            
            # Generate wave points. 
            # We iterate across the canvas width, but calculate Y based on GLOBAL x (global_offset + x)
            # This ensures that the wave continues perfectly from the previous screen.
            step = 5
            for x in range(-stroke_width, width + stroke_width + step, step):
                global_x = global_offset + x
                
                # Apply envelope: amplitude tapers to 0 at both ends (global_x=0 and global_x=total_width)
                # Using sin envelope: 0 at edges, 1 at center
                envelope_ratio = global_x / total_width  # 0 to 1 across the panorama
                envelope = math.sin(envelope_ratio * math.pi)  # 0 -> 1 -> 0
                
                # Angle is based on global_x relative to a single screen width (for frequency scaling)
                angle = (global_x / width) * 2 * math.pi * freq_mult + phase
                y = base_y + (amplitude * envelope) * math.sin(angle)
                points.append((x, y))
            
            # Draw the wave line
            if len(points) > 1:
                draw.line(points, fill=rgba_color, width=stroke_width)
