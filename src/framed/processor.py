import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from .config import Config

from .templates.standard import StandardTemplate
from .templates.panoramic import PanoramicTemplate

class Processor:
    def __init__(self, config: Config):
        self.config = config
        self.bezel_path = Path(__file__).parent.parent.parent / "resources" / "bezel.png"
        
        # Select Template
        if config.template == 'panoramic':
            self.template = PanoramicTemplate(config)
            print("  🎨 Using Panoramic Template")
        else:
            self.template = StandardTemplate(config)
            print("  🎨 Using Standard Template")
        
        # Device specific constants for bezel composition
        self.SCREENSHOT_WIDTH = 1206
        self.SCREENSHOT_HEIGHT = 2622

    def process(self):
        """Apply frames and text to extracted screenshots."""
        raw_dir = Path(self.config.output_dir) / "raw"
        final_dir = Path(self.config.output_dir) / "framed"
        
        screenshot_config = self.config.raw_config.get('screenshots', {})
        if not screenshot_config:
            print("⚠️ No 'screenshots' config found. Skipping processing.")
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
                    key = img_path.stem 
                    
                    if key in screenshot_config:
                        meta = screenshot_config[key]
                        self._process_image(img_path, dst_dir, meta, lang, key, screenshot_config)
                    else:
                        print(f"  Skipping {key} (no config entry)")

    def _create_device_frame(self, screenshot):
        """Create device frame by compositing screenshot with bezel."""
        if not self.bezel_path.exists():
            raise FileNotFoundError(f"Bezel file not found at {self.bezel_path}")
        
        bezel = Image.open(self.bezel_path).convert("RGBA")
        
        if bezel.width >= screenshot.width and bezel.height >= screenshot.height:
            frame = Image.new('RGBA', bezel.size, (0, 0, 0, 0))
            
            sx = (bezel.width - screenshot.width) // 2
            sy = (bezel.height - screenshot.height) // 2
            
            mask = Image.new('L', screenshot.size, 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle((0, 0, screenshot.width, screenshot.height), radius=80, fill=255)
            
            frame.paste(screenshot, (sx, sy), mask)
            frame.paste(bezel, (0, 0), bezel)
            return frame
        else:
            raise ValueError(f"Bezel {bezel.size} is smaller than screenshot {screenshot.size}")

    def _process_image(self, img_path: Path, output_dir: Path, meta: dict, lang: str, key: str, screenshots_config: dict):
        # Load Screenshot
        screenshot = Image.open(img_path).convert('RGBA')
        
        # Prepare Device Frame (Bezel composition happens here for now)
        # Future: Move bezel composition into a DeviceManager or Template if needed
        screenshot_resized = screenshot.resize((self.SCREENSHOT_WIDTH, self.SCREENSHOT_HEIGHT), Image.Resampling.LANCZOS)
        device_frame = self._create_device_frame(screenshot_resized)
        
        # Prepare Text Config
        defaults = self.config.template_defaults or {}
        
        text_config = {
            'title_text': meta.get('title', {}).get(lang, ""),
            'subtitle_text': meta.get('subtitle', {}).get(lang, ""),
            'background_color': meta.get('background_color') or defaults.get('background_color', '#F5F5F7'),
            'text_color': meta.get('text_color') or defaults.get('text_color', '#1D1D1F'),
            'subtitle_color': meta.get('subtitle_color') or defaults.get('subtitle_color', '#86868B'),
            # Panoramic specific config
            'panoramic_color': meta.get('panoramic_color') or defaults.get('panoramic_color', '#C7C7CC')
        }
        
        # Calculate Index and Total for Panoramic Context
        # We need to find the index of this screenshot in the ordered config list
        screenshot_keys = list(screenshots_config.keys())
        try:
            current_index = screenshot_keys.index(key)
        except ValueError:
            current_index = 0
        total_screenshots = len(screenshot_keys)    

        # Delegate to Template
        final_image = self.template.process(
            screenshot, 
            text_config, 
            device_frame, 
            index=current_index, 
            total=total_screenshots
        )
        
        # Save
        out_path = output_dir / img_path.name
        final_image.save(out_path, quality=95)
        print(f"  ✅ Generated {out_path.name}")
