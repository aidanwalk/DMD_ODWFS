
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

import display

global DisplaySize
DisplaySize = (1080, 1920)  # (height, width) in pixels
global intensity; intensity = 0

class Set(Enum):
    Disabled = 0
    Enabled = 1



class Intensity_Screen:
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
        
        
    def __call__(self, *args, **kwargs):
        return self.generate_screen(*args, **kwargs)



    


    def generate_screen(self, intensity=0):
        """
        Generate an flat screen (all one intensitty) between 0 to 255 in intensity
        With offsets right and up to shift the ramp.
        
        parameters
        ----------
        intensity: int
            The intensity of the screen, between 0 and 255.
        returns
        -------
        screen: np.ndarray
            The generated screen pattern as a 2D numpy array (shape = self.image_size).
        """
        
        screen = np.zeros(self.dmd_size, dtype=f'uint{self.bit_depth}')
        screen[:] = display.intensity2hex(intensity)
        # Scale the screen to the image size
        screen = zoom(screen, (self.image_size[0] / self.dmd_size[0], self.image_size[1] / self.dmd_size[1]), order=0, prefilter=False)
        return screen
    
    





def StreamFrameBuffer():
    global buf, screen, intensity
    while True:
        # create a 32 bit image
        image = screen(intensity)  # Change intensity as needed
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


def main():
    global mode
    # Define the shapes to display
    global screen
    screen = Intensity_Screen()
    
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
    
    
    print("Entering main loop. Enter 'q' to quit.")
    
    
    # Listen for keyboard input
    while loop:
        ans = input("Enter intensity (0-255) or 'q' to quit: ")
        if ans.lower() == 'q':
            loop = False
        else:
            try:
                intensity = int(ans)
                if 0 <= intensity <= 255:
                    image = screen(intensity)
                else:
                    print("Invalid intensity. Please enter a value between 0 and 255.")
            except ValueError:
                print("Invalid input. Please enter a number between 0 and 255.")

    # ######## END TASK ########
    time.sleep(0.5)
    buf[:] = 0x00000000
    # turn on the cursor again:    
    os.system("TERM=linux setterm -foreground white -clear all >/dev/tty0")
    i2c.terminate()



if __name__ == "__main__": main()







# # ===========================================================================
# # Uncomment the following lines to run the script as a standalone program
# # This will allow you to visualize the screen functionality using matplotlib.
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
    
#     screen = Intensity_Screen()
#     pattern = screen(intensity=255)
#     image = argb_to_rgb_array(pattern)
    
    
#     plt.figure(figsize=(10,7), tight_layout=True)
#     plt.title("Ramp Pattern")
#     plt.ion()
    
#     pim = plt.imshow(image, cmap='gray', vmin=0, vmax=2**screen.bit_depth - 1)
#     plt.colorbar()
#     plt.show()
    
    
#     while True:
#         cmd = input("Enter screen intensity (0-255), 'q' to quit")
#         if cmd.lower() == 'q':
#             break
#         try:
#             intensity = int(cmd)
#             if 0 <= intensity <= 255:
#                 pattern = screen(intensity)
#                 image = argb_to_rgb_array(pattern)
#                 pim.set_data(image)
#                 plt.draw()
#                 plt.pause(0.01)
#             else:
#                 print("Invalid intensity. Please enter a value between 0 and 255.")
#         except ValueError:
#             print("Invalid input. Please enter a number between 0 and 255.")

#     plt.ioff()
#     plt.close()

        
        
