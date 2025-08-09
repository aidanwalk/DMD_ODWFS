import numpy as np
from scipy.ndimage import zoom

import display

class Ramp:
    """
    A class to generate ramp knife edges on the DMD. 
    
    ** WARNING ** 
    This class fails to generate odd-valued ramp widths. 
    
    parameters:
    -----------
    dmd_size: tuple
        The number of DMD mirrors in (height, width).
    image_size: tuple
        The size of the image to be projected in (height, width).
        (i.e. the frame size expected by the Raspberry Pi framebuffer)
    bit_depth: int
        The bit depth of the Raspberry Pi framebuffer.
        (i.e. 2**(bit_depth) - 1 is the maximum value of a pixel == white)
    """
    def __init__(self, 
                 dmd_size=(540,960),
                 image_size=(1080, 1920), 
                 bit_depth=32):
        
        self.dmd_size = dmd_size
        self.image_size = image_size
        self.bit_depth = bit_depth
        self.reverse_perception = True

        self.edge = 0
        self.edge_generator = [self.Edge_1, 
                               self.Edge_2, 
                               self.Edge_3, 
                               self.Edge_4
                               ]
        
        
    def __call__(self, *args, **kwargs):
        return self.generate_ramp(*args, **kwargs)

    
    def generate_ramp(self, width=10, right=0, up=0):
        """
        Generate a ramp pattern from 0 to 2**(bit_depth) - 1.
        With offsets right and up to shift the ramp.
        
        parameters
        ----------
        width: int
            The width of the ramp in DMD mirrors.
        right: int
            The number of DMD mirrors to shift the ramp to the right.
        up: int
            The number of DMD mirrors to shift the ramp up.
            
        returns
        -------
        ramp: np.ndarray
            The generated ramp pattern as a 2D numpy array (shape = self.image_size).
        """
        
        ramp = self.edge_generator[self.edge](
            cx=self.dmd_size[1]//2 + right, 
            cy=self.dmd_size[0]//2 + up,
            width=width
        )
        # Scale the ramp to the image size
        ramp = zoom(ramp, (self.image_size[0] / self.dmd_size[0], self.image_size[1] / self.dmd_size[1]), order=0, prefilter=False)
        return ramp
    


    def generate_greyscale_hex_colors(self, n):
        # Generate grayscale values from 0 to 255 (8-bit range for RGB components)
        gray_vals = np.linspace(0, 255, n, dtype=np.uint8)
        
        # Create uint32 colors directly
        uint_32_colors = [display.intensity2hex(g, reverse_perception=self.reverse_perception) for g in gray_vals]

        return np.array(uint_32_colors, dtype=np.uint32)



    def Edge_1(self, cx, cy, width=10):
        """
        Generates ramp edge 1 of the knife edge (right edge):
            |  #|
            |  #|
            
        parameters
        ----------
        cx: int
            The center x position of the ramp in DMD mirrors.
        width: int
            The width of the ramp in DMD mirrors.
            
        returns
        -------
        ramp: np.ndarray
            The generated ramp pattern as a 2D numpy array (shape = self.dmd_size).
        """
        ramp = np.zeros(self.dmd_size, dtype=f'uint{self.bit_depth}')
        
        # Calculate the start and end positions of the ramp
        start_x = cx - width // 2
        end_x   = cx + width // 2
        
        if width % 2 == 1:
            # If width is odd, adjust the end position to include the center mirror
            end_x += 1
            # print("** WARNING ** Odd ramp width injects a tilt aberration. (The ramp cannot be centered between pixels)")
        
        
        start_x = max(start_x, 0)
        end_x = min(end_x, self.dmd_size[1])
        if start_x < 0 or end_x > self.dmd_size[1]:
            raise ValueError("Ramp width exceeds DMD size. Please adjust the width or center position.")
        
        
        # Generate the ramp values
        # ramp_values = np.linspace(0, 2**self.bit_depth - 1, end_x - start_x, dtype=f'uint{self.bit_depth}')
        ramp_values = self.generate_greyscale_hex_colors(end_x - start_x)
        # print(f"Ramp values: {ramp_values}")
        
        # Assign the ramp values to the appropriate row in the ramp array
        ramp[:, start_x:end_x] = ramp_values
        # Set values to the right of the ramp to white
        ramp[:, end_x:] = 2**self.bit_depth - 1
        return ramp
    
    
    
    def Edge_2(self, cx, cy, width=10):
        """
        Generates ramp edge 2 of the knife edge (left edge):
            |#  |
            |#  |
            
        parameters
        ----------
        cx: int
            The center x position of the ramp in DMD mirrors.
        width: int
            The width of the ramp in DMD mirrors.
            
        returns
        -------
        ramp: np.ndarray
            The generated ramp pattern as a 2D numpy array (shape = self.dmd_size).
        """
        ramp = np.zeros(self.dmd_size, dtype=f'uint{self.bit_depth}')
        
        # Calculate the start and end positions of the ramp
        start_x = cx - width // 2
        end_x   = cx + width // 2
        
        if width % 2 == 1:
            # If width is odd, adjust the end position to include the center mirror
            end_x += 1
            # print("** WARNING ** Odd ramp width injects a tilt aberration. (The ramp cannot be centered between pixels)")
        
        
        start_x = max(start_x, 0)
        end_x = min(end_x, self.dmd_size[1])
        if start_x < 0 or end_x > self.dmd_size[1]:
            raise ValueError("Ramp width exceeds DMD size. Please adjust the width or center position.")
        
        
        # Generate the ramp values
        # ramp_values = np.linspace(0, 2**self.bit_depth - 1, end_x - start_x, dtype=f'uint{self.bit_depth}')
        ramp_values = self.generate_greyscale_hex_colors(end_x - start_x)
        # print(f"Ramp values: {ramp_values}")
        
        # Assign the ramp values to the appropriate row in the ramp array
        ramp[:, start_x:end_x] = ramp_values[::-1]  # Reverse the order for left edge
        # Set values to the right of the ramp to white
        ramp[:, :start_x] = 2**self.bit_depth - 1
        return ramp
    
    
    def Edge_3(self, cx, cy, width=10):
        """
        Generates ramp edge 3 of the knife edge (top edge):
            |####|
            |    | 
        
        """
        ramp = np.zeros(self.dmd_size, dtype=f'uint{self.bit_depth}')
        
        # Calculate the start and end positions of the ramp
        start_y = cy - width // 2
        end_y   = cy + width // 2
        
        if width % 2 == 1:
            # If width is odd, adjust the end position to include the center mirror
            end_y += 1
            # print("** WARNING ** Odd ramp width injects a tilt aberration. (The ramp cannot be centered between pixels)")
        
        
        start_y = max(start_y, 0)
        end_y = min(end_y, self.dmd_size[0])
        if start_y < 0 or end_y > self.dmd_size[0]:
            raise ValueError("Ramp width exceeds DMD size. Please adjust the width or center position.")
        
        # Generate the ramp values
        # ramp_values = np.linspace(0, 2**self.bit_depth - 1, end_y - start_y, dtype=f'uint{self.bit_depth}')
        ramp_values = self.generate_greyscale_hex_colors(end_y - start_y)

        # Assign the ramp values to the appropriate column in the ramp array
        ramp[start_y:end_y, :] = ramp_values[:, np.newaxis]
        # Set values above the ramp to white
        ramp[end_y:, :] = 2**self.bit_depth - 1
        return ramp
    
    
    
    def Edge_4(self, cx, cy, width=10):
        """
        Generates ramp edge 4 of the knife edge (bottom edge):
            |    |
            |####|
        
        """
        ramp = np.zeros(self.dmd_size, dtype=f'uint{self.bit_depth}')
        
        # Calculate the start and end positions of the ramp
        start_y = cy - width // 2
        end_y   = cy + width // 2
        
        if width % 2 == 1:
            # If width is odd, adjust the end position to include the center mirror
            end_y += 1
            # print("** WARNING ** Odd ramp width injects a tilt aberration. (The ramp cannot be centered between pixels)")
        
        
        start_y = max(start_y, 0)
        end_y = min(end_y, self.dmd_size[0])
        if start_y < 0 or end_y > self.dmd_size[0]:
            raise ValueError("Ramp width exceeds DMD size. Please adjust the width or center position.")
        
        # Generate the ramp values
        # ramp_values = np.linspace(0, 2**self.bit_depth - 1, end_y - start_y, dtype=f'uint{self.bit_depth}')
        ramp_values = self.generate_greyscale_hex_colors(end_y - start_y)

        # Assign the ramp values to the appropriate column in the ramp array
        ramp[start_y:end_y, :] = ramp_values[::-1, np.newaxis]
        # Set values above the ramp to white
        ramp[:start_y, :] = 2**self.bit_depth - 1
        return ramp
    
    

    def change_edge(self, edge_id):
        """
        Change the edge generator function.
        
        parameters
        ----------
        edge_id: int
            The edge id to use (1, 2, 3, or 4).
        """
        if edge_id in [1, 2, 3, 4]:
            self.edge = edge_id - 1
            print(f"Edge changed to {edge_id}")
            return
        else:
            raise ValueError("Invalid edge id. Please use 1, 2, 3, or 4.")
    
    
    def change_to_edge_1(self):
        self.change_edge(1)
        
    def change_to_edge_2(self):
        self.change_edge(2)
        
    def change_to_edge_3(self):
        self.change_edge(3)
        
    def change_to_edge_4(self):
        self.change_edge(4)



