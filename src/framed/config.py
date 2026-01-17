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
    font_bold: str = None
    font_regular: str = None

def load_config(path: str = "framed.yaml") -> Config:
    """Load configuration from a YAML file"""
    if not Path(path).exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    # Parse root objects
    config_section = data.get('config', {})
    
    return Config(
        project=config_section.get('project'),
        scheme=config_section.get('scheme'),
        output_dir=config_section.get('output_dir', 'docs/screenshots'),
        font_bold=config_section.get('font_bold'),
        font_regular=config_section.get('font_regular'),
        devices=data.get('devices', []),
        languages=data.get('languages', ['en']),
        raw_config=data
    )
