from PIL import Image, ImageDraw, ImageFont
from ...api import Template
from ...config import Config

class StandardTemplate(Template):
    """
    The standard "Text Top + Device Bottom" layout.
    Ported from original KOE workflow.
    """
    
    def __init__(self, config: Config):
        self.config = config
        
        # Layout Constants
        self.CANVAS_WIDTH = 1350
        self.CANVAS_HEIGHT = 2868
        self.SCREENSHOT_WIDTH = 1206
        self.SCREENSHOT_HEIGHT = 2622
        self.HEADER_MARGIN = 200
        self.LINE_SPACING = 30
        self.CAPTION_SPACING = 60
        self.PHONE_TOP_OFFSET = 150
        self.APP_STORE_SIZE = (1290, 2796)

    def process(self, screenshot: Image.Image, text_config: dict, device_frame: Image.Image | None = None, index: int = 0, total: int = 1) -> Image.Image:
        # Configuration
        bg_color = text_config.get('background_color', '#F5F5F7')
        text_color = text_config.get('text_color', '#1D1D1F')
        subtitle_color = text_config.get('subtitle_color', '#86868B')
        
        # Create canvas
        canvas = Image.new('RGB', (self.CANVAS_WIDTH, self.CANVAS_HEIGHT), bg_color)
        draw = ImageDraw.Draw(canvas)
        
        # === Draw Text ===
        current_y = self._draw_text(draw, text_config)
            
        # === Place Device ===
        if device_frame:
             # Position Phone: Using FIXED layout logic (same as Panoramic)
             # This ensures device size/pos is constant regardless of actual text length
             
             # Fonts (Load here to calculate fixed height)
             # Reuse helper or load directly. To avoid modifying _load_font visibility/signature risks, just load again.
             # It's quick.
             title_font = self._load_font(95, bold=True)
             subtitle_font = self._load_font(45, bold=False)

            # Simulate max text height (Max 2 lines for Title, 1 for Subtitle)
             max_title_lines = 2
            
             dummy_line_h = draw.textbbox((0, 0), "Aj", font=title_font)[3] - draw.textbbox((0, 0), "Aj", font=title_font)[1]
             fixed_title_h = max_title_lines * (dummy_line_h + self.LINE_SPACING)
            
             dummy_sub_h = draw.textbbox((0, 0), "Aj", font=subtitle_font)[3] - draw.textbbox((0, 0), "Aj", font=subtitle_font)[1]
            
             fixed_text_bottom = self.HEADER_MARGIN + fixed_title_h + (self.CAPTION_SPACING - self.LINE_SPACING) + dummy_sub_h
            
             compact_offset = 110
             phone_y = fixed_text_bottom + compact_offset
            
             phone_x = (self.CANVAS_WIDTH - device_frame.width) // 2
            
             # Dynamic scaling if device doesn't fit
             remaining_height = self.CANVAS_HEIGHT - phone_y
             if device_frame.height > remaining_height:
                 scale = (remaining_height - 100) / device_frame.height
                 if scale < 1.0:
                     new_w = int(device_frame.width * scale)
                     new_h = int(device_frame.height * scale)
                     device_frame = device_frame.resize((new_w, new_h), Image.Resampling.LANCZOS)
                     phone_x = (self.CANVAS_WIDTH - new_w) // 2
            
             canvas.paste(device_frame, (phone_x, int(phone_y)), device_frame)

        # Final Resize
        return canvas.resize(self.APP_STORE_SIZE, Image.Resampling.LANCZOS)

    def _draw_text(self, draw: ImageDraw.ImageDraw, text_config: dict) -> int:
        text_color = text_config.get('text_color', '#1D1D1F')
        subtitle_color = text_config.get('subtitle_color', '#86868B')
        title = text_config.get('title_text', "")
        subtitle = text_config.get('subtitle_text', "")
        
        # Fonts
        title_font = self._load_font(95, bold=True)
        subtitle_font = self._load_font(45, bold=False)
        
        current_y = self.HEADER_MARGIN
        
        # Title
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
        if subtitle:
            bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
            w = bbox[2] - bbox[0]
            draw.text(((self.CANVAS_WIDTH - w) / 2, current_y), subtitle, font=subtitle_font, fill=subtitle_color)
            current_y += bbox[3] - bbox[1]
            
        return current_y

    def _load_font(self, size: int, bold: bool = False):
        # ... logic ported from processor.py ...
        # Ideally this should be a utility helper, but for now we keep it here or pass from processor
        # To avoid duplicating logic, we might want to move font loading to a helper or keep it here.
        # For simplicity in this step, I'll copy the font loading logic but refer to self.config
        
        # Reusing the exact logic from existing processor.py
        import os
        candidates = []
        if bold and self.config.font_bold: candidates.append(self.config.font_bold)
        elif not bold and self.config.font_regular: candidates.append(self.config.font_regular)
        
        if bold: candidates.extend(["/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc", "/System/Library/Fonts/Hiragino Sans GB.ttc"])
        else: candidates.extend(["/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc", "/System/Library/Fonts/Hiragino Sans GB.ttc"])
            
        for path in candidates:
            if os.path.exists(path):
                try:
                    index = 0 if path.endswith('.ttc') else 0
                    return ImageFont.truetype(path, size, index=index)
                except Exception: continue
        return ImageFont.load_default()

