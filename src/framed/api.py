from abc import ABC, abstractmethod
from pathlib import Path
from PIL import Image

class Template(ABC):
    """Abstract base class for screenshot templates."""
    
    @abstractmethod
    def process(self, screenshot: Image.Image, text_config: dict, device_frame: Image.Image | None = None) -> Image.Image:
        """
        Process a single screenshot into a final marketing image.
        
        Args:
            screenshot: The raw screenshot image (from simulator)
            text_config: Dictionary containing title, subtitle, colors, etc.
            device_frame: Optional pre-composited device frame (if handled externally) or bezel info
            
        Returns:
            The final composed image ready for saving.
        """
        pass
