from abc import ABC, abstractmethod
from pathlib import Path
from PIL import Image

class Template(ABC):
    """Abstract base class for screenshot templates."""
    
    @abstractmethod
    def process(self, screenshot: Image.Image, text_config: dict, device_frame: Image.Image | None = None, index: int = 0, total: int = 1) -> Image.Image:
        """
        Process the screenshot and applying the template layout.
        
        Args:
            screenshot: The raw screenshot image
            text_config: Dictionary containing text and style configuration
            device_frame: Optional pre-processed device frame
            index: The index of the current screenshot in the sequence (0-based)
            total: The total number of screenshots in the sequence
            
        Returns:
            The final composed image ready for saving.
        """
        pass
