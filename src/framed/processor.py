import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from .config import Config

from .templates.standard import StandardTemplate
from .templates.panoramic import PanoramicTemplate
from .templates.perspective import PerspectiveTemplate

class Processor:
    def __init__(self, config: Config):
        self.config = config
        self.bezel_path = Path(__file__).parent.parent.parent / "resources" / "bezel.png"

        
        # Select Template
        if config.template == 'panoramic':
            self.template = PanoramicTemplate(config)
            print("  🎨 Using Panoramic Template")
        elif config.template == 'perspective':
            self.template = PerspectiveTemplate(config)
            print("  🎨 Using Perspective Template")
        else:
            self.template = StandardTemplate(config)
            print("  🎨 Using Standard Template")
        
        # Device specific constants for bezel composition
        self.SCREENSHOT_WIDTH = 1206
        self.SCREENSHOT_HEIGHT = 2622
    
    def _resolve_text(self, text_map: dict | str | None, lang: str) -> str:
        """
        Resolve text for a given language with fallback.
        e.g. if lang is 'en-US' but map only has 'en', it will return 'en' value.
        """
        if not text_map:
            return ""
        
        if isinstance(text_map, str):
            return text_map
            
        # 1. Exact match
        val = text_map.get(lang)
        if val is not None: 
            return val
        
        # 2. Base language fallback (en-US -> en)
        if '-' in lang:
            base_lang = lang.split('-')[0]
            val = text_map.get(base_lang)
            if val is not None:
                return val
                
        return ""

    def process(self):
        """Apply frames and text to extracted screenshots."""
        # Use custom raw_dir if specified, otherwise default to output_dir/raw
        if self.config.raw_dir:
            raw_dir = Path(self.config.raw_dir)
        else:
            raw_dir = Path(self.config.output_dir) / "raw"
        
        final_dir = Path(self.config.output_dir) / "framed"
        
        screenshot_config = self.config.raw_config.get('screenshots', {})
        if not screenshot_config:
            print("⚠️ No 'screenshots' config found. Skipping processing.")
            return



        for device in self.config.devices:
            dev_name = device['name']
            for lang in self.config.languages:
                # If raw_dir is set and points to a specific directory, use it directly
                # Otherwise use the traditional {device}_{lang} naming
                if self.config.raw_dir and not dev_name:
                    # raw_dir points directly to screenshots (e.g., raw_samples/ja/)
                    # lang might be empty string to avoid double suffix
                    src_dir = raw_dir
                    # For output, use a clean name
                    output_suffix = lang if lang else "ja"  # Fallback to 'ja' if lang is empty
                    dst_dir = final_dir / output_suffix
                else:
                    # Traditional behavior: raw/device_lang/
                    src_dir = raw_dir / f"{dev_name}_{lang}"
                    dst_dir = final_dir / f"{dev_name}_{lang}"
                

                if not src_dir.exists():
                    continue
                    
                print(f"🎨 Processing {dev_name} ({lang})...")
                dst_dir.mkdir(parents=True, exist_ok=True)
                
                # Check for group-based processing
                if self.config.groups:
                    self._process_groups(src_dir, dst_dir, screenshot_config, lang)

                # Process individual screenshots (always check, don't fallback)
                # Iterate through CONFIG items, not files, to support source_key aliasing
                for key, meta in screenshot_config.items():
                    source_key = meta.get('source_key', key)
                    img_path = src_dir / f"{source_key}.png"
                    
                    if not img_path.exists():
                         # Only warn if it's NOT part of a group? 
                         # Actually usually we want silent skip for things used only in groups, 
                         # BUT here we are iterating config. If it's in config, we expect to process it.
                         # However, some keys ("onboarding") might be JUST for groups and have no output config?
                         # In samples framed.yaml, "onboarding" is in screenshots.
                         # If it's in screenshots, we try to process it.
                         # If image missing, we skip.
                         print(f"  Skipping {key} (Source image {source_key}.png not found)")
                         continue
                         
                    self._process_image(img_path, dst_dir, meta, lang, key, screenshot_config)

    def _process_groups(self, src_dir: Path, output_dir: Path, screenshot_config: dict, lang: str):
        """Process screenshots as defined groups (for composite templates)."""
        for group in self.config.groups:
            output_name = group.get('output', 'output.png')
            screen_keys = group.get('screens', [])
            group_template_name = group.get('template', self.config.template)
            
            # Collect device frames and text configs for this group
            device_frames = []
            text_configs = []
            
            for key in screen_keys:
                img_path = src_dir / f"{key}.png"
                if not img_path.exists():
                    print(f"  ⚠️ Image not found: {key}.png, skipping from group")
                    continue
                
                meta = screenshot_config.get(key, {})
                
                # Load and prepare device frame
                screenshot = Image.open(img_path).convert('RGBA')
                screenshot_resized = screenshot.resize((self.SCREENSHOT_WIDTH, self.SCREENSHOT_HEIGHT), Image.Resampling.LANCZOS)
                device_frame = self._create_device_frame(screenshot_resized)
                device_frames.append(device_frame)
                
                # Prepare text config
                defaults = self.config.template_defaults or {}
                text_config = defaults.copy()
                
                # Merge group configuration (allows passing custom params like panorama_index)
                text_config.update(group)
                
                if 'background_color' in meta: text_config['background_color'] = meta['background_color']
                if 'text_color' in meta: text_config['text_color'] = meta['text_color']
                if 'subtitle_color' in meta: text_config['subtitle_color'] = meta['subtitle_color']
                if 'panoramic_color' in meta: text_config['panoramic_color'] = meta['panoramic_color']
                if 'panoramic_color' in meta: text_config['panoramic_color'] = meta['panoramic_color']
                
                # Resolve text with fallback
                text_config['title_text'] = self._resolve_text(meta.get('title'), lang)
                text_config['subtitle_text'] = self._resolve_text(meta.get('subtitle'), lang)
                
                text_configs.append(text_config)
            
            if not device_frames:
                print(f"  ⚠️ No valid frames for group '{output_name}', skipping")
                continue
            
            # Select template for this group
            # Currently only PerspectiveTemplate supports groups specifically
            if group_template_name == 'perspective':
                # Re-instantiate to ensure fresh state if needed, or stick with self.template if it is PerspectiveTemplate
                if isinstance(self.template, PerspectiveTemplate):
                    template = self.template
                else:
                    template = PerspectiveTemplate(self.config)
                    
                final_image = template.process_group(device_frames, text_configs, lang)
            else:
                # For non-group-aware templates, process first screen only as fallback
                final_image = self.template.process(None, text_configs[0], device_frames[0], 0, 1)
            
            # Save
            out_path = output_dir / output_name
            final_image.save(out_path, quality=95)
            print(f"  ✅ Generated {output_name}")

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
        
        # Start with a copy of defaults (so we inherit everything like perspective_tilt)
        text_config = defaults.copy()
        
        # Override with meta (screenshot specific config)
        if 'background_color' in meta: text_config['background_color'] = meta['background_color']
        if 'text_color' in meta: text_config['text_color'] = meta['text_color']
        if 'subtitle_color' in meta: text_config['subtitle_color'] = meta['subtitle_color']
        if 'panoramic_color' in meta: text_config['panoramic_color'] = meta['panoramic_color']
        
        # Add text content
        text_config['title_text'] = self._resolve_text(meta.get('title'), lang)
        text_config['subtitle_text'] = self._resolve_text(meta.get('subtitle'), lang)
        
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
        # Prefix with index to ensure order (e.g. 01_inbox.png)
        # Use 1-based indexing for display
        # Prefix with index to ensure order (e.g. 01_inbox.png)
        # Use 1-based indexing for display
        # If output file name is specified (e.g. custom key), use that.
        # But for list generation, we often want numbering.
        # However, if 'key' is "1", "2", etc., use that directly.
        
        if key.isdigit():
            out_filename = f"{key}.png"
        else:
            prefix = f"{current_index + 1:02d}_"
            out_filename = prefix + key + ".png"
            
        out_path = output_dir / out_filename
        final_image.save(out_path, quality=95)
        print(f"  ✅ Generated {out_path.name}")
