

import os
import numpy as np
import time
import threading
import i2c

# TI DMD API

import sys, os.path
python_dir = (os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(python_dir)
from api.dlpc343x_xpr4 import *


from parallel_mode import make_parallel_mode


# DMD control and display
from ramp_pattern import Ramp
from sshkeyboard import listen_keyboard, stop_listening


# -----------------------------------------------------------------------------
# ========== DISPLAY SETTINGS ==========
# DISPLAY SIZE FOR THE FRAMEBUFFER
# YOU PROBABLY SHOULD NOT CHANGE THIS
global DisplaySize
DisplaySize = (1080, 1920)  # (height, width)
# -----------------------------------------------------------------------------



# ----------------------------------------------------------------------------
# ============ GLOBAL VARIABLES =============
# Ramp pattern object
global ramp; ramp = Ramp()
# Offeset of the ramp pattern from the center of the DMD
global right, up; right, up = 0, 0
# Width of the ramp (i.e. 2*modulation radius)
global ramp_width; ramp_width = 960//2
# Mirror lock status
global locked; locked = False
# Initial step size for moving the shape
global step; step=100


global mode
# Available modes for the DLPDLCR230NPEVM
# Each mode corresponds to a function that changes the display.
# The keys are the characters that the user can input to select the mode.
# The values are the functions that will be called when the user selects the mode.


# -----------------------------------------------------------------------------



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
    def PrintOffset():
        """
        Prints the current offset of the shape.
        This is useful for debugging and understanding the current position of the shape.
        """
        global right, up
        print(f"Current offset: x={right}, y={up}")
        return None

    @staticmethod
    def Cycle_Width():    
        """
        Cycles through the step sizes: 1, 10, 100.
        This allows the user to change the step size for moving the shape.
        """
        global ramp_width

        def change_width_1():
            ramp_width = 1
            print(f'Width changed to {ramp_width}')
            return ramp_width

        def change_width_4():
            ramp_width = 4
            print(f'Width changed to {ramp_width}')
            return ramp_width

        def change_width_8():
            ramp_width = 8
            print(f'Width changed to {ramp_width}')
            return ramp_width


        if ramp_width == 1: ramp_width = change_width_4()
        elif ramp_width == 4: ramp_width = change_width_8()
        else: ramp_width = change_width_1()
        
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
            return step

        def change_step_10():
            step = 10
            print(f'Step size changed to {step}')
            return step

        def change_step_100():
            step = 100
            print(f'Step size changed to {step}')
            return step
        
        
        if step == 1: step = change_step_10()
        elif step == 10: step = change_step_100()
        else: step = change_step_1()
        
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
        chars_to_check = 'uqrmo'
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
       
       

        
def Menu():
    menu = """
----------------------------------
               MENU                
----------------------------------
 w      Cycle Ramp Width
        (cycles through 1, 4, 8)
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
    'w'     : Cmd.Cycle_Width,
    '1'     : ramp.change_to_edge_1,
    '2'     : ramp.change_to_edge_2,
    '3'     : ramp.change_to_edge_3,
    '4'     : ramp.change_to_edge_4,
    'o'     : Cmd.PrintOffset,
}


def StreamFrameBuffer():
    global buf, ramp, ramp_width, up, right
    while True:
        # create a 32 bit image
        image = ramp(width=ramp_width, right=right, up=up)
        # image = square()
        # push to screen
        buf[:] = image
        time.sleep(0.1)


      

def initialize_offsets():
    init_offset = input("Enter the initial offset (x,y) in pixels (default is 0,0): ")
    if init_offset:
        try:
            right, up = map(int, init_offset.split(','))
            print(f"Initial offset set to x={right}, y={up}")
        except ValueError:
            print("Invalid input. Using default offset of x=0, y=0.")
            right = 0
            up = 0
    else:
        print("Using default offset of x=0, y=0.")
        right = 0
        up = 0
        
    return right, up



def main():
    print("Initializing parallel mode...")
    make_parallel_mode()
    # this turns off the cursor blink:
    os.system ("TERM=linux setterm -foreground black -clear all >/dev/tty0")



    # this is the frambuffer for analog video output - note that this is a 32 bit RGB
    # other setups will likely have a different format and dimensions which you can check with
    # fbset -fb /dev/fb0 
    # The last two numbers of "geometry" are the bit depth
    global buf
    buf = np.memmap('/dev/fb0', dtype='uint32',mode='w+', shape=DisplaySize)

    # fill with white
    buf[:] = 0xffffffff



    # ######## START TASK ########
    
    loop = True
    global stop; stop = False
    
    right, up = initialize_offsets()
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
    # Listen for keyboard input
    while loop:
        listen_keyboard(on_press=Cmd.Call,
                        delay_second_char=0.05,
                        delay_other_chars=0.05,)
        loop = False
        
    
    # ######## END TASK ########
    Cmd.UnlockMirrors()
    time.sleep(0.5)
    buf[:] = 0x00000000
    # turn on the cursor again:    
    os.system("TERM=linux setterm -foreground white -clear all >/dev/tty0")
    i2c.terminate()



if __name__ == "__main__": main()







# # ===========================================================================
# # Uncomment the following lines to run the script as a standalone program
# # This will allow you to visualize the ramp pattern using matplotlib.
# # ===========================================================================



# def argb_to_rgb_array(argb_values):
#     # Function is used to convert ARGB values to RGB array
#     # (Rpi pixel format is hex ARGB. Matplotlib expects RGB)
#     # Extract RGB components from ARGB
#     red = (argb_values >> 16) & 0xFF
#     green = (argb_values >> 8) & 0xFF
#     blue = argb_values & 0xFF
    
#     # Stack into RGB array and normalize to 0-1 range
#     rgb_array = np.stack([red, green, blue], axis=-1) / 255.0
#     return rgb_array


# if __name__ == "__main__":
#     import matplotlib.pyplot as plt
    
#     width = 5
#     edge_id = 1
#     ramp = Ramp()
#     pattern = ramp(width=width, right=0, up=0)
#     image = argb_to_rgb_array(pattern)
    
#     plt.figure(figsize=(10,7), tight_layout=True)
#     plt.title("Ramp Pattern")
#     plt.ion()
    
#     # pim = plt.imshow(image, cmap='gray', vmin=0, vmax=2**ramp.bit_depth - 1)
#     x, y = np.arange(image.shape[1]), np.mean(image, axis=(0, 2))
#     print(x.shape, y.shape)
#     pim = plt.plot(x, y, color='k', linewidth=2)
#     # plt.colorbar()
#     plt.show()
    
#     while True:
#         cmd = input("Enter Edge (1-4), ramp width (w), or Q to quit: ")
#         if cmd.lower() == 'q':
#             break
#         elif cmd.lower() == 'w':
#             width = int(input("Enter new ramp width: "))
#             print(f"Ramp width set to {width}")
#         elif cmd.isnumeric():
#             edge_id = int(cmd)
            
#         try:
#             # edge_id = int(cmd)
#             ramp.change_edge(edge_id)
#             pattern = ramp(width=width, right=0, up=0)
#             image = argb_to_rgb_array(pattern)
#             # pim.set_data(image)
#             x, y = np.arange(image.shape[1]), np.mean(image, axis=(2, 0))
#             # Update the scatter plot with new data
#             plt.clf()
#             pim = plt.plot(x, y, color='k', linewidth=2)
#             plt.title(f"Ramp Pattern - Edge {edge_id}, Width {width}")
#             plt.draw()
#             plt.pause(0.01)
#         except ValueError as e:
#             print(e)
#             continue
    
#     plt.ioff()
#     plt.close()

        
        
