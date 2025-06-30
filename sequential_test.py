"""
This script is used to display a sequential knife edge or sequential pyramid
test pattern on to the DMD. 

It is designed to be run on a Raspberry Pi with a DLPDLCR230NPEVM
connected to it. It uses the framebuffer to display the patterns on the DMD.
It allows you to move the shape around the screen, change the step size, 
change the shape, and lock/unlock the mirrors.


[k] Knife Edge Test (default)
    ---------------
    Commands a knife edge pattern in the following order:
    1. +X    |  ##|
             |  ##|
        
    2. -X    |##  |
             |##  |
             
    3. +Y    |####|
             |    |
             
    4. -Y    |    |
             |####|
             
    *where # indicates a mirror in the ON state. 


[p] Pyramid Test
    ------------
    Commands a pyramid pattern in the following order:
    1. +X,+Y    |  #|
                |   |
        
    2. -X,+Y    |#  |
                |   |
             
    3. -X,-Y    |   |
                |#  |
             
    4. +X,-Y    |   |
                |  #|
                
    *where # indicates a mirror in the ON state. 
    


Use:
----
1. Ensure the DLPDLCR230NPEVM is connected to the Raspberry Pi.
2. DLPDLCR230NPEVM is powered on and ready.
3. Run the script:
   $ python sequential.py
4. Find the center of the PSF on the DMD. 
   If you know the center coordinates apriori, enter them when prompted at the
   start of the script. Otherwise, use the arrow keys to move the shape
   around the screen until you find the center of the PSF.
5. Use the ' ' keys to cycle through the knife edges




Streaming to the Raspberry Pi Frame Buffer from Quasimondo 2025-06-19
https://gist.github.com/Quasimondo/e47a5be0c2fa9a3ef80c433e3ee2aead

@author: Aidan Walk, walka@hawaii.edu

"""

import time
import asyncio
import numpy as np
import os
import threading
import matplotlib.pyplot as plt

from enum import Enum

import sys, os.path
python_dir = (os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(python_dir)
from api.dlpc343x_xpr4 import *
from api.dlpc343x_xpr4_evm import *
from linuxi2c import *
import i2c

from sshkeyboard import listen_keyboard, stop_listening

# ===============================================================================
# GLOBAL VARIABLES -- CHANGE ME
# ===============================================================================
# Set the display size to match your framebuffer resolution
# This must match resolution listed from:
#     $ fbset -fb /dev/fb0
# "geometry"
global DisplaySize; DisplaySize = (1080, 1920)
# Initial step size for moving the shape
global step; step=100
# ===============================================================================


class Set(Enum):
    Disabled = 0
    Enabled = 1


class Cmd():
    @staticmethod
    def LockMirrors():
        '''
        Locks the mirrors on the DLPDLCR230NPEVM.
        This is useful for freezing the DMD mirrors.
        '''
        global locked
        Summary = WriteMirrorLock(MirrorLockOptions.DmdInterfaceLock)
        print("Mirrors locked.")
        locked = True
        return Summary

    @staticmethod
    def RetryLock():
        '''
        Retries to lock the mirrors on the DMD. 
        Often times you may get unlucky and lock the mirrors on the wrong side of 
        the duty cycle. 
        
        Quickly unlocks the mirros and then locks them again.
        '''
        global locked
        if not locked:
            print("The mirrors were not locked.")
            Cmd.LockMirrors()
        
        else:
            Cmd.UnlockMirrors()
            time.sleep(0.25)
            Summary = Cmd.LockMirrors()
            return Summary

    @staticmethod
    def UnlockMirrors():
        '''
        Unlocks the mirrors on the DLPDLCR230NPEVM.
        This is useful for unfreezing the DMD mirrors.
        '''
        global locked
        Summary = WriteMirrorLock(MirrorLockOptions.DmdInterfaceUnlock)
        print("Mirrors unlocked.")
        locked = False
        return Summary

    @staticmethod
    def MoveUp():
        global up
        up += step
        print(f"Offset: x={right}, y={up}")
        return None
    
    @staticmethod
    def MoveDown():
        global up
        up -= step
        print(f"Offset: x={right}, y={up}")
        return None
    
    @staticmethod
    def MoveRight():
        global right
        right += step
        print(f"Offset: x={right}, y={up}")
        return None
    
    @staticmethod
    def MoveLeft():
        global right
        right -= step
        print(f"Offset: x={right}, y={up}")
        return None

    @staticmethod
    def Cycle_Step():    
        """
        Cycles through the step sizes: 1, 10, 100.
        This allows the user to change the step size for moving the shape.
        """
        global step
        
        def change_step_1():
            step = 1
            print(f'Step size changed to {step}')
            return None

        def change_step_10():
            global step
            step = 10
            print(f'Step size changed to {step}')
            return None

        def change_step_100():
            global step
            step = 100
            print(f'Step size changed to {step}')
            return step
        
        
        if step == 1: change_step_10()
        elif step == 10: change_step_100()
        else: change_step_1()
        
        return None


    @staticmethod
    def Quit():
        stop_listening()
        print("Exiting...")
        return None

    @staticmethod
    def Call(key):
        """
        Calls the function associated with the name.
        """
        global locked, mode
        chars_to_check = 'uqrm'
        # If we are not unlocking the mirrors or quitting,
        # check if the mirrors are locked. 
        # If they are locked, we cannot change the display.
        if not any(char in key for char in chars_to_check) and locked: 
            print("Mirrors are locked. Please unlock them first.")
            return None
        
        # Otherwise, change the display if a valid option is selected
        if key not in mode:
            print("Invalid option. Please try again.")
            return Menu()
        
        func = mode[key]
        return func()
        



class knife:
    def __init__(self, cx=DisplaySize[1]//2, cy=DisplaySize[0]//2):
        """Create a knife image with a given center."""
        # Create an empty array with the specified size
        global right, up
        self.cx = DisplaySize[1] // 2
        self.cy = DisplaySize[0] // 2
        self.edge_func = self.edge1
        
    def __call__(self):
        """ Call the knife object to get the image."""
        return self.get_image()
    
    def edge1(self):
        """ Create an image of edge 1 """
        y0 = 0
        y1 = DisplaySize[0]
        x0 = self.cx
        x1 = DisplaySize[1]
        return y0, y1, x0, x1
    
    def edge2(self):
        """ Create an image of edge 2 """
        y0 = 0
        y1 = DisplaySize[0]
        x0 = 0
        x1 = self.cx
        return y0, y1, x0, x1
    
    def edge3(self):
        """ Create an image of edge 3 """
        y0 = self.cy
        y1 = DisplaySize[0]
        x0 = 0
        x1 = DisplaySize[1]
        return y0, y1, x0, x1
    
    def edge4(self):
        """ Create an image of edge 4 """
        y0 = 0
        y1 = self.cy
        x0 = 0
        x1 = DisplaySize[1]
        return y0, y1, x0, x1
    
    def get_image(self):
        global right, up
        self.cx = DisplaySize[1] // 2 + right
        self.cy = DisplaySize[0] // 2 + up
        img = np.zeros(DisplaySize, dtype='uint32')
        start_y, end_y, start_x, end_x = self.edge_func()
        # Fill the image area with white color (255, 255, 255)
        img[start_y:end_y, start_x:end_x] = 0xffffffff #2**32-1
        
        return img
    
    
    
class pyramid:
    def __init__(self, cx=DisplaySize[1]//2, cy=DisplaySize[0]//2):
        """Create a knife image with a given center."""
        # Create an empty array with the specified size
        global right, up
        self.cx = DisplaySize[1] // 2
        self.cy = DisplaySize[0] // 2
        self.edge_func = self.edge1
        
    def __call__(self):
        """Call the pyramid object to get the image."""
        return self.get_image()
    
    def edge1(self):
        """ Create an image of edge 1 """
        y0 = self.cy
        y1 = DisplaySize[0]
        x0 = self.cx
        x1 = DisplaySize[1]
        return y0, y1, x0, x1
    
    def edge2(self):
        """ Create an image of edge 2 """
        y0 = self.cy
        y1 = DisplaySize[0]
        x0 = 0
        x1 = self.cx
        return y0, y1, x0, x1
    
    def edge3(self):
        """ Create an image of edge 3 """
        y0 = 0
        y1 = self.cy
        x0 = 0
        x1 = self.cx
        return y0, y1, x0, x1
    
    def edge4(self):
        """ Create an image of edge 4 """
        y0 = 0
        y1 = self.cy
        x0 = self.cx
        x1 = DisplaySize[1]
        return y0, y1, x0, x1
    
    def get_image(self):
        global right, up
        self.cx = DisplaySize[1] // 2 + right
        self.cy = DisplaySize[0] // 2 + up
        img = np.zeros(DisplaySize, dtype='uint32')
        start_y, end_y, start_x, end_x = self.edge_func()
        # Fill the image area with white color (255, 255, 255)
        img[start_y:end_y, start_x:end_x] = 0xffffffff #2**32-1
        
        return img



class shapes:
    """
    A class to hold the shapes to display.
    This is used to create a list of shapes that can be displayed.
    """
    def __init__(self):
        self.k = knife()
        self.p = pyramid()
        self.shape = self.k


    def change_to_knife(self):
        self.shape = self.k
        
    def change_to_pyramid(self):
        self.shape = self.p

    # def __len__(self):
    #     return len(self.shapes)
    
    def reset_shapes(self):
        """
        Resets the shapes to the initial state.
        """
        global right, up
        right = 0
        up = 0
        return None
    
    
    def change_to_edge_1(self):
        self.shape.edge_func = self.shape.edge1
        
    def change_to_edge_2(self):
        self.shape.edge_func = self.shape.edge2

    def change_to_edge_3(self):
        self.shape.edge_func = self.shape.edge3
        
    def change_to_edge_4(self):
        self.shape.edge_func = self.shape.edge4




def StreamFrameBuffer():
    global pim, DisplaySize, shape_maker
    while True:
        # create a 32 bit image
        image = shape_maker.shape()
        # image = square()
        # push to screen
        # buf[:] = image
        
        pim.set_data(image)
        plt.draw()
        plt.pause(0.1)
        

def make_plot():
    
    plt.figure(figsize=(10, 6))
    plt.axis('off')  # Hide the axes
    plt.title("DLPDLCR230NPEVM Display")
    pim = plt.imshow(np.zeros(DisplaySize, dtype='uint32'), cmap='gray', origin='lower')
    plt.ion()  # Turn on interactive mode
    plt.show()
    return pim

      
def Menu():
    menu = """
----------------------------------
               MENU                
----------------------------------
 p      Sequential Pyramid Mode
 k      Sequential Knife Edge Mode
 1      Edge 1
 2      Edge 2
 3      Edge 3
 4      Edge 4
 s      Change step size 
        (cycles through 1, 10, 100)
 right  Move Right
 left   Move Left             
 up     Move Up
 down   Move Down
 l      Lock Mirrors
 r      Retry Lock
 u      Unlock Mirrors
 m      Display Menu
 q      Quit                        
----------------------------------
    """
    print(menu)
    return None



def main():
    global mode
    # Define the shapes to display
    global shape_maker
    shape_maker = shapes()
    # Available modes for the DLPDLCR230NPEVM
    # Each mode corresponds to a function that changes the display.
    # The keys are the characters that the user can input to select the mode.
    # The values are the functions that will be called when the user selects the mode.
    mode = {
        'up'    : Cmd.MoveUp, 
        'down'  : Cmd.MoveDown,
        'left'  : Cmd.MoveLeft,
        'right' : Cmd.MoveRight,
        'l'     : Cmd.LockMirrors,
        'r'     : Cmd.RetryLock,
        'u'     : Cmd.UnlockMirrors,
        'q'     : Cmd.Quit,
        'm'     : Menu,
        's'     : Cmd.Cycle_Step,
        'k'     : shape_maker.change_to_knife,
        'p'     : shape_maker.change_to_pyramid,
        '1'     : shape_maker.change_to_edge_1,
        '2'     : shape_maker.change_to_edge_2,
        '3'     : shape_maker.change_to_edge_3,
        '4'     : shape_maker.change_to_edge_4,
    }

    
    
    # Enable screen parallel mode
    print("Initializing parallel mode...")
    global pim
    pim = make_plot()
    
    
    # ######## START TASK ########
    
    loop = True
    global stop; stop = False
    global right, up
    right = 0
    up = 0
    global locked; locked = False
    global sq_size
    # Thread to run StreamFrameBuffer
    print("Creating StreamFrameBuffer thread...")
    # Create a thread to run the StreamFrameBuffer function
    # This will allow the framebuffer to be updated in the background
    # while we can still interact with the main program
    threading1 = threading.Thread(target=StreamFrameBuffer)
    threading1.daemon = True  # This allows the thread to exit when the main program exits
    threading1.name = "StreamFrameBuffer"
    print("Starting StreamFrameBuffer thread...")
    # start the thread
    threading1.start()
    time.sleep(0.5)
    Menu()
    
        
    
    # ######## END TASK ########
    sq_size = 0
    time.sleep(0.5)



if __name__ == "__main__": main()
