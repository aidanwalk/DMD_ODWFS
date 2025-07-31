
import time
import numpy as np
from scipy.ndimage import zoom
import os
import threading

from enum import Enum

import sys, os.path
python_dir = (os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(python_dir)
from api.dlpc343x_xpr4 import *
from api.dlpc343x_xpr4_evm import *
from linuxi2c import *
import i2c

from sshkeyboard import listen_keyboard, stop_listening


global DisplaySize
DisplaySize = (1080, 1920)  # (height, width) in
# Initial step size for moving the shape
global step; step=100

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
        



class Ramp:
    """
    A class to generate ramp knife edges on the DMD. 
    
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
        
        self.edge = 0
        self.edge_generator = [self.Edge_1, 
                               self.Edge_2, 
                               self.Edge_3, 
                               self.Edge_4
                               ]
        
        
    def __call__(self, *args, **kwargs):
        return self.generate_ramp(*args, **kwargs)


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
        

    @staticmethod
    def generate_greyscale_hex_colors(n):
        # Grayscale values from 0 to 255
        gray_vals = np.linspace(0, 255, n, dtype=np.uint8)
        
        hex_colors = []
        for g in gray_vals:
            # Convert to 32-bit ARGB: full alpha (0xFF), and equal RGB
            color = (0xFF << 24) | (g << 16) | (g << 8) | g
            hex_colors.append(f'0x{color:08X}')

        # Convert hex values to uint 32
        uint_32_colors = np.array([int(color, 16) for color in hex_colors])

        return uint_32_colors


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
        start_x = max(cx - width // 2, 0)
        end_x = min(cx + width // 2, self.dmd_size[1])
        
        # Generate the ramp values
        # ramp_values = np.linspace(0, 2**self.bit_depth - 1, end_x - start_x, dtype=f'uint{self.bit_depth}')
        ramp_values = self.generate_greyscale_hex_colors(end_x - start_x)
        
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
        # Just invert edge 1
        return 2**self.bit_depth - 1 - self.Edge_1(cx, cy, width)
    
    
    def Edge_3(self, cx, cy, width=10):
        """
        Generates ramp edge 3 of the knife edge (top edge):
            |####|
            |    | 
        
        """
        ramp = np.zeros(self.dmd_size, dtype=f'uint{self.bit_depth}')
        
        # Calculate the start and end positions of the ramp
        start_y = max(cy - width // 2, 0)
        end_y = min(cy + width // 2, self.dmd_size[0])
        
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
        # Just invert edge 3
        return 2**self.bit_depth - 1 - self.Edge_3(cx, cy, width)
    
    
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
    
    
    def change_to_edge_1(self):
        self.change_edge(1)
        
    def change_to_edge_2(self):
        self.change_edge(2)
        
    def change_to_edge_3(self):
        self.change_edge(3)
        
    def change_to_edge_4(self):
        self.change_edge(4)







def StreamFrameBuffer():
    global buf, ramp, ramp_width, up, right
    while True:
        # create a 32 bit image
        image = ramp(width=ramp_width, right=right, up=up)
        # image = square()
        # push to screen
        buf[:] = image
        time.sleep(0.1)




def make_parallel_mode():
        '''
        Initializes the Raspberry Pi's GPIO lines to communicate with the DLPDLCR230NPEVM,
        and configures the DLPDLCR2OA30NPEVM to project RGB666 parallel video input received from the Raspberry Pi.
        '''

        gpio_init_enable = True          # Set to FALSE to disable default initialization of Raspberry Pi GPIO pinouts. TRUE by default.
        i2c_time_delay_enable = False    # Set to FALSE to prevent I2C commands from waiting. May lead to I2C bus hangups with some commands if FALSE.
        i2c_time_delay = 0.8             # Lowering this value will speed up I2C commands. Too small delay may lead to I2C bus hangups with some commands.
        protocoldata = ProtocolData()

        def WriteCommand(writebytes, protocoldata):
            '''
            Issues a command over the software I2C bus to the DLPDLCR230NP EVM.
            Set to write to Bus 7 by default
            Some commands, such as Source Select (splash mode) may perform asynchronous access to the EVM's onboard flash memory.
            If such commands are used, it is recommended to provide appropriate command delay to prevent I2C bus hangups.
            '''
            # print ("Write Command writebytes ", [hex(x) for x in writebytes])
            if(i2c_time_delay_enable): 
                time.sleep(i2c_time_delay)
            i2c.write(writebytes)       
            return

        def ReadCommand(readbytecount, writebytes, protocoldata):
            '''
            Issues a read command over the software I2C bus to the DLPDLCR230NP EVM.
            Set to read from Bus 7 by default
            Some commands, such as Source Select (splash mode) may perform asynchronous access to the EVM's onboard flash memory.
            If such commands are used, it is recommended to provide appropriate command delay to prevent I2C bus hangups.
            '''
            # print ("Read Command writebytes ", [hex(x) for x in writebytes])
            if(i2c_time_delay_enable): 
                time.sleep(i2c_time_delay)
            i2c.write(writebytes) 
            readbytes = i2c.read(readbytecount)
            return readbytes

        # ##### ##### Initialization for I2C ##### #####
        # register the Read/Write Command in the Python library
        DLPC343X_XPR4init(ReadCommand, WriteCommand)
        i2c.initialize()
        if(gpio_init_enable): 
            InitGPIO()
        # ##### ##### Command call(s) start here ##### #####  

        print("Setting DLPC3436 Input Source to Raspberry Pi...")
        Summary = WriteDisplayImageCurtain(1,Color.Black)
        Summary = WriteSourceSelect(Source.ExternalParallelPort, Set.Disabled)
        Summary = WriteInputImageSize(1920, 1080)

        print("Configuring DLPC3436 Source Settings for Raspberry Pi...")
        Summary = WriteActuatorGlobalDacOutputEnable(Set.Enabled)
        Summary = WriteExternalVideoSourceFormatSelect(ExternalVideoFormat.Rgb666)
        Summary = WriteVideoChromaChannelSwapSelect(ChromaChannelSwap.Cbcr)
        Summary = WriteParallelVideoControl(ClockSample.FallingEdge,  Polarity.ActiveHigh,  Polarity.ActiveLow,  Polarity.ActiveLow)
        Summary = WriteColorCoordinateAdjustmentControl(0)
        Summary, BitRate, PixelMapMode = ReadFpdLinkConfiguration()
        Summary = WriteDelay(50)
        time.sleep(1)
        Summary = WriteDisplayImageCurtain(0,Color.Black)


      
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
    global mode
    # Define the shapes to display
    global ramp
    ramp = Ramp()
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
        'w'     : Cmd.Cycle_Width,
        '1'     : ramp.change_to_edge_1,
        '2'     : ramp.change_to_edge_2,
        '3'     : ramp.change_to_edge_3,
        '4'     : ramp.change_to_edge_4,
        'o'     : Cmd.PrintOffset,
    }

    
    
    # Enable screen parallel mode
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
    
    global right, up
    right, up = initialize_offsets()
    global ramp_width; ramp_width = 1
    
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
    # Listen for keyboard input
    while loop:
        listen_keyboard(on_press=Cmd.Call,
                        delay_second_char=0.05,
                        delay_other_chars=0.05,)
        loop = False
        
    
    # ######## END TASK ########
    Cmd.UnlockMirrors()
    sq_size = 0
    time.sleep(0.5)
    buf[:] = 0x00000000
    # turn on the cursor again:    
    os.system("TERM=linux setterm -foreground white -clear all >/dev/tty0")
    i2c.terminate()



if __name__ == "__main__": main()









"""

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    
    width = 5
    ramp = Ramp()
    pattern = ramp(width=width, right=0, up=0)
    
    
    plt.figure(figsize=(10,7), tight_layout=True)
    plt.title("Ramp Pattern")
    plt.ion()
    
    pim = plt.imshow(pattern, cmap='gray', vmin=0, vmax=2**ramp.bit_depth - 1)
    plt.colorbar()
    plt.show()
    
    while True:
        cmd = input("Enter Edge (1-4) or Q to quit: ")
        if cmd.lower() == 'q':
            break
        try:
            edge_id = int(cmd)
            ramp.change_edge(edge_id)
            pattern = ramp(width=width, right=0, up=0)
            pim.set_data(pattern)
            plt.draw()
            plt.pause(0.01)
        except ValueError as e:
            print(e)
            continue
    
    plt.ioff()
    plt.close()

        
        
"""