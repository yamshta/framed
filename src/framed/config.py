from dataclasses import dataclass
import yaml
from pathlib import Path
from typing import List, Dict, Any

@dataclass
class Config:
    project: str
    scheme: str
    output_dir: str
    devices: List[Dict[str, str]]
    languages: List[str]
    raw_config: Dict[str, Any]
    raw_dir: str | None = None  # Optional custom raw directory path
    font_bold: str = None
    font_regular: str | None = None
    template: str = 'standard'
    template_defaults: Dict[str, Any] = None
    groups: List[Dict[str, Any]] = None  # For multi-device cascade output

def load_config(path: str = "framed.yaml") -> Config:
    """Load configuration from a YAML file"""
    if not Path(path).exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    # Parse root objects
    config_section = data.get('config', {})
    
    # Template Configuration (Root level preferred, fallback to config section)
    template_name = data.get('template') or config_section.get('template', 'standard')
    
    # Load Template Defaults
    template_config_path = Path(__file__).parent / "templates" / template_name / "template.yaml"
    template_defaults = {}
    
    if template_config_path.exists():
        try:
            with open(template_config_path, 'r', encoding='utf-8') as f:
                tmpl_data = yaml.safe_load(f)
                template_defaults = tmpl_data.get('defaults', {})
        except Exception as e:
            print(f"⚠️ Failed to load template config: {e}")

    # Merge Global Template Settings
    # Root level 'template_settings' preferred, fallback to config section
    user_template_settings = data.get('template_settings') or config_section.get('template_settings', {})
    if user_template_settings:
        template_defaults.update(user_template_settings)

    # Merge Defaults into Global Config (User config overrides defaults)
    # We don't overwrite the 'raw_config' directly because it preserves structure,
    # but we can inject defaults into the 'config' section if missing?
    # Better approach: We pass 'template_defaults' to the Config object or merge them now.
    
    # Let's merge defaults into 'config_section' for global settings
    # And we also need to apply these defaults to each screenshot if not present?
    # Actually, Processor does the lookup. So if we put defaults in 'raw_config', Processor can find them?
    # No, Processor looks at 'meta' (screenshot config). It falls back to defaults if not found.
    # So we should inject template_defaults into the Config object so Processor can use them as fallback.
    
    return Config(
        project=config_section.get('project'),
        scheme=config_section.get('scheme'),
        output_dir=config_section.get('output_dir', 'docs/screenshots'),
        raw_dir=config_section.get('raw_dir'),  # Optional custom raw directory
        font_bold=config_section.get('font_path_title') or config_section.get('font_bold'),
        font_regular=config_section.get('font_path_subtitle') or config_section.get('font_regular'),
        template=template_name,
        devices=data.get('devices', []),
        languages=data.get('languages', ['en']),
        raw_config=data, # Keeps original structure
        template_defaults=template_defaults, # New field
        groups=data.get('groups', None)  # Multi-device cascade groups
    )
