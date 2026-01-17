import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from .config import Config

class Processor:
    def __init__(self, config: Config):
        self.config = config
        # Bezel path (relative to framed package root)
        self.bezel_path = Path(__file__).parent.parent.parent / "resources" / "bezel.png"
        
        # Layout Constants
        self.CANVAS_WIDTH = 1350
        self.CANVAS_HEIGHT = 2868
        self.SCREENSHOT_WIDTH = 1206
        self.SCREENSHOT_HEIGHT = 2622
        self.HEADER_MARGIN = 200
        self.LINE_SPACING = 30
        self.CAPTION_SPACING = 60
        self.PHONE_TOP_OFFSET = 150  # Space between text and device

    def process(self):
        """Apply frames and text to extracted screenshots."""
        raw_dir = Path(self.config.output_dir) / "raw"
        final_dir = Path(self.config.output_dir) / "framed"
        
        screenshot_config = self.config.raw_config.get('screenshots', {})
        if not screenshot_config:
            print("⚠️ No 'screenshots' config found in framed.yaml. Skipping processing.")
            return

        for device in self.config.devices:
            dev_name = device['name']
            for lang in self.config.languages:
                src_dir = raw_dir / f"{dev_name}_{lang}"
                dst_dir = final_dir / f"{dev_name}_{lang}"
                
                if not src_dir.exists():
                    continue
                    
                print(f"🎨 Processing {dev_name} ({lang})...")
                dst_dir.mkdir(parents=True, exist_ok=True)
                
                for img_path in src_dir.glob("*.png"):
                    key = img_path.stem # e.g. "inbox"
                    
                    # Check if we have config for this screen
                    if key in screenshot_config:
                        meta = screenshot_config[key]
                        self._process_image(img_path, dst_dir, meta, lang)
                    else:
                        print(f"  Skipping {key} (no config entry)")

    def _create_device_frame(self, screenshot):
        """Create device frame by compositing screenshot with bezel."""
        if not self.bezel_path.exists():
            raise FileNotFoundError(f"Bezel file not found at {self.bezel_path}")
        
        bezel = Image.open(self.bezel_path).convert("RGBA")
        
        # Check if bezel matches expected device
        if bezel.width >= screenshot.width and bezel.height >= screenshot.height:
            # Perfect case: Bezel matches target device
            frame = Image.new('RGBA', bezel.size, (0, 0, 0, 0))
            
            # Center offset
            sx = (bezel.width - screenshot.width) // 2
            sy = (bezel.height - screenshot.height) // 2
            
            # 1. Mask Screenshot (Round Corners) to prevent overflow outside bezel
            mask = Image.new('L', screenshot.size, 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle((0, 0, screenshot.width, screenshot.height), radius=80, fill=255)
            
            # 2. Paste Screenshot with mask
            frame.paste(screenshot, (sx, sy), mask)
            
            # 3. Paste Bezel on top (to cover edges/island area correctly)
            frame.paste(bezel, (0, 0), bezel)
            
            return frame
        else:
            raise ValueError(f"Bezel {bezel.size} is smaller than screenshot {screenshot.size}")

    def _process_image(self, img_path: Path, output_dir: Path, meta: dict, lang: str):
        """Process a single screenshot with bezel and text overlay."""
        # Load Screenshot
        screenshot = Image.open(img_path).convert('RGBA')
        
        # Configuration
        bg_color = meta.get('background_color', '#F5F5F7')
        text_color = meta.get('text_color', '#1D1D1F')
        subtitle_color = meta.get('subtitle_color', '#86868B')
        
        # Create canvas
        canvas = Image.new('RGB', (self.CANVAS_WIDTH, self.CANVAS_HEIGHT), bg_color)
        draw = ImageDraw.Draw(canvas)
        
        # Get title and subtitle from config
        title = meta.get('title', {}).get(lang, "")
        subtitle = meta.get('subtitle', {}).get(lang, "")
        
        # Load Hiragino fonts
        title_font = self._load_hiragino_font(95, bold=True)  # W8
        subtitle_font = self._load_hiragino_font(45, bold=False)  # W6
        
        # === Draw Text ===
        current_y = self.HEADER_MARGIN
        
        # Title (Centered, multi-line support)
        if title:
            lines = title.split('\n')
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=title_font)
                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]
                draw.text(((self.CANVAS_WIDTH - w) / 2, current_y), line, font=title_font, fill=text_color)
                current_y += h + self.LINE_SPACING
        
        current_y += (self.CAPTION_SPACING - self.LINE_SPACING)
        
        # Subtitle (Centered)
        if subtitle:
            bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
            w = bbox[2] - bbox[0]
            draw.text(((self.CANVAS_WIDTH - w) / 2, current_y), subtitle, font=subtitle_font, fill=subtitle_color)
            current_y += bbox[3] - bbox[1]
        
        # === Create Device Frame ===
        # Resize screenshot to expected dimensions
        screenshot_resized = screenshot.resize((self.SCREENSHOT_WIDTH, self.SCREENSHOT_HEIGHT), Image.Resampling.LANCZOS)
        device_frame = self._create_device_frame(screenshot_resized)
        
        # Position Phone: Below text with offset
        phone_y = current_y + self.PHONE_TOP_OFFSET
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
        
        # Paste device frame onto canvas
        canvas.paste(device_frame, (phone_x, phone_y), device_frame)
        
        # === Final Resize to App Store Standard ===
        # App Store requires 1290x2796 for iPhone 15 Pro Max (6.7")
        # Our working canvas is 1350x2868, so resize down
        APP_STORE_SIZE = (1290, 2796)
        canvas_resized = canvas.resize(APP_STORE_SIZE, Image.Resampling.LANCZOS)
        
        # Save
        out_path = output_dir / img_path.name
        canvas_resized.save(out_path, quality=95)
        print(f"  ✅ Generated {out_path.name}")

    def _load_hiragino_font(self, size: int, bold: bool = False):
        """Load configured font or fallback to Hiragino/Defaults."""
        candidates = []
        
        # 1. Configured fonts
        if bold and self.config.font_bold:
            candidates.append(self.config.font_bold)
        elif not bold and self.config.font_regular:
            candidates.append(self.config.font_regular)
            
        # 2. System defaults (macOS Hiragino)
        if bold:
            candidates.extend([
                "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc",
                "/System/Library/Fonts/Hiragino Sans GB.ttc",
            ])
        else:
            candidates.extend([
                "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
                "/System/Library/Fonts/Hiragino Sans GB.ttc",
            ])
        
        for path in candidates:
            if os.path.exists(path):
                try:
                    # TTC files need index specification
                    index = 0 if path.endswith('.ttc') else 0
                    return ImageFont.truetype(path, size, index=index)
                except Exception:
                    continue
        
        # Fallback to default
        print(f"⚠️ Font not found, using default")
        return ImageFont.load_default()
