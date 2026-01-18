import numpy as np
from PIL import Image, ImageDraw
from ...api import Template
from ...config import Config
from ..standard import StandardTemplate

def find_coeffs(source_coords, target_coords):
    """
    Calculate coefficients for perspective transformation.
    source_coords: [(x,y), (x,y), (x,y), (x,y)] - TopLeft, TopRight, BottomRight, BottomLeft
    target_coords: [(x,y), (x,y), (x,y), (x,y)] - TopLeft, TopRight, BottomRight, BottomLeft
    """
    matrix = []
    for s, t in zip(source_coords, target_coords):
        matrix.append([t[0], t[1], 1, 0, 0, 0, -s[0]*t[0], -s[0]*t[1]])
        matrix.append([0, 0, 0, t[0], t[1], 1, -s[1]*t[0], -s[1]*t[1]])

    A = np.matrix(matrix, dtype=float)
    B = np.array(source_coords).reshape(8)

    res = np.dot(np.linalg.inv(A.T * A) * A.T, B)
    return np.array(res).reshape(8)

class PerspectiveTemplate(StandardTemplate):
    """
    A hybrid template:
    - Index 0-2: Tilted perspective flow (3D-like connected look).
    - Index 3+: Standard flat layout.
    """
    
    def process(self, screenshot: Image.Image, text_config: dict, device_frame: Image.Image | None = None, index: int = 0, total: int = 1) -> Image.Image:
        # Fallback to Standard layout for 4th screen onwards
        if index >= 3:
            return super().process(screenshot, text_config, device_frame, index, total)

        # === Perspective Logic for Index 0-2 ===
        
        # 1. Config & Colors
        bg_color = text_config.get('background_color', '#F5F5F7')
        
        # 2. Canvas
        canvas = Image.new('RGB', (self.CANVAS_WIDTH, self.CANVAS_HEIGHT), bg_color)
        draw = ImageDraw.Draw(canvas)
        
        # 3. Text (Same as Standard)
        self._draw_text(draw, text_config)
        
        # 4. Prepare Device Image
        if device_frame:
             # device_frame already has screenshot and bezel composited.
             flat_device = device_frame
        else:
             # Fallback if no bezel
             flat_device = screenshot.resize((1206, 2622), Image.LANCZOS)

        # 5. Calculate Perspective Transform
        # We want to tilt it.
        # Let's define a "Tilted Right" look.
        # Source points (Rectangular)
        w, h = flat_device.size
        src_points = [(0, 0), (w, 0), (w, h), (0, h)]
        
        # Target points (Trapezoid)
        # We simulate a rotation around Y axis.
        # Top-Left: Moved Right & Down
        # Top-Right: Moved Left & Down (compressed)
        # Bottom-Right: Moved Left & Up (compressed)
        # Bottom-Left: Moved Right & Up
        
        # Simple skew/perspective parameters
        # Index 0: Leftmost
        # Index 1: Center
        # Index 2: Rightmost
        
        # Let's stagger them horizontally.
        # Index 0: X offset -300
        # Index 1: X offset 0
        # Index 2: X offset +300
        
        offset_x = (index - 1) * 200 # -200, 0, 200
        
        # Base coordinate for the "Center" of the perspective device
        center_x = self.CANVAS_WIDTH // 2 + offset_x
        center_y = self.CANVAS_HEIGHT // 2 + 100
        
        # Perspective scaling (make it look 3D)
        scale = 0.85
        
        # Tilt amount (Delta X for top/bottom edges)
        tilt = 150 
        
        # Target Width/Height after scaling
        tw = w * scale
        th = h * scale
        
        # Coordinates relative to center
        # Top-Left
        tl = (center_x - tw/2 + tilt, center_y - th/2 + 100)
        # Top-Right
        tr = (center_x + tw/2 - tilt, center_y - th/2) # Farther away visually? NO, assume simple tilt
        # Let's iterate on the exact coordinates.
        # For a simple "facing right" tilt:
        # Left edge is taller/closer, Right edge is shorter/farther.
        
        # Let's try:
        # TL: (x, y)
        # TR: (x + w, y + delta_y)  -- skewed down
        # BR: (x + w, y + h - delta_y) -- skewed up
        # BL: (x, y + h)
        
        # Implementation of "Tilted Back-Right"
        #   /|
        #  | |
        #  | |
        #   \|
        
        pad = 200
        
        p_tl = (0, 0)
        p_tr = (tw, 150)
        p_br = (tw, th - 150)
        p_bl = (0, th)
        
        # Center this shape on canvas
        shape_w = tw
        shape_h = th
        
        base_x = (self.CANVAS_WIDTH - shape_w) // 2
        base_y = self.PHONE_TOP_OFFSET + 100 # Lower than standard title
        
        # Apply Staggering based on index
        # 0: Left (-), 1: Center, 2: Right (+)
        # Actually user wants them "connected".
        # Maybe they join at the edges?
        # Let's just stagger them for now.
        stagger_x = (index - 1) * 300
        base_x += stagger_x

        dst_points = [
            (base_x + p_tl[0], base_y + p_tl[1]),
            (base_x + p_tr[0], base_y + p_tr[1]),
            (base_x + p_br[0], base_y + p_br[1]),
            (base_x + p_bl[0], base_y + p_bl[1])
        ]
        
        coeffs = find_coeffs(dst_points, src_points)
        
        # Transform
        # Use a large enough buffer for rotation/transform
        buffer = Image.new('RGBA', (self.CANVAS_WIDTH, self.CANVAS_HEIGHT), (0,0,0,0))
        
        # We need to transform the *source* onto the *destination*
        # Image.transform expects data to be coefficients to map dest -> source
        transformed = flat_device.transform(
            (self.CANVAS_WIDTH, self.CANVAS_HEIGHT),
            Image.PERSPECTIVE,
            coeffs,
            Image.BICUBIC,
            fillcolor=None
        )
        
        # Paste onto canvas
        canvas.paste(transformed, (0, 0), transformed)
        
        return canvas

