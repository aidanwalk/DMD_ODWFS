import numpy as np

from pupilary_response import pupilary_response



def intensity2hex(intensity, reverse_perception=False):
    """
    Convert greyscale intensity (0-255) to 32-bit ARGB hex color.
    The intensity should be in the range [0, 255].
    
    Parameters:
    -----------
    intensity : uint8
        Greyscale intensity value (0-255).
        
    Returns:
    --------
    uint32
        32-bit ARGB color value.
    """
    if not (0 <= intensity <= 255):
        raise ValueError("Intensity must be in the range [0, 255]")
    
    if reverse_perception:
        # Apply reverse perception correction if specified
        intensity = pupilary_response.reverse_perception_correction(intensity / 255.0) * 255
        intensity = np.clip(intensity, 0, 255)
    
    intensity = np.uint8(intensity)
    
    # Convert to 32-bit ARGB: full alpha (0xFF), and equal RGB components
    # Each component is 8-bit, so intensity should be 0-255
    alpha = np.uint32(0xFF) << 24  # Full alpha
    red = np.uint32(intensity) << 16       # Red component
    green = np.uint32(intensity) << 8      # Green component
    blue = np.uint32(intensity)            # Blue component
    
    uint_32_color = alpha | red | green | blue

    return uint_32_color