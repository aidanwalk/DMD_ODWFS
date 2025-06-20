"""
Taken from Quasimondo 2025-06-19
https://gist.github.com/Quasimondo/e47a5be0c2fa9a3ef80c433e3ee2aead
"""
# After a lot of searching and false or complicated leads I found this brilliant method
# that allows to use a numpy array to get direct read/write access to the rpi framebuffer
# https://stackoverflow.com/questions/58772943/how-to-show-an-image-direct-from-memory-on-rpi
# I thought it is worth sharing again since so it might someone else some research time
#
# The only caveat is that you will have to run this as root (sudo python yourscript.py), 
# But you can get around this if you add the current user to the "video" group like this:
# usermod -a -G video [user]
# source: https://medium.com/@avik.das/writing-gui-applications-on-the-raspberry-pi-without-a-desktop-environment-8f8f840d9867
# 
# in order to clear the cursor you probably also have to add the user to the tty group
# usermod -a -G tty [user]
# Potentially also to the dialout group (not so sure about that, but I did it before I realized that a reboot is required)
# usermod -a -G dialout [user]
# IMPORTANT you will have to reboot once for this to take effect
import struct
import time
import numpy as np
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
from test import LockMirrors, UnlockMirrors, RetryLock

from sshkeyboard import listen_keyboard

# Set the display size to match your framebuffer resolution
global DisplaySize; DisplaySize = (1080, 1920)



class Set(Enum):
    Disabled = 0
    Enabled = 1



def press(key):
    global right, up
    if key == 'right':
        right += 10
    elif key == 'left':
        right -= 10
    elif key == 'up':
        up += 10
    elif key == 'down':
        up -= 10
    elif key == 'l':
        print("Locking mirrors...")
        LockMirrors()
    elif key == 'u':
        print("Unlocking mirrors...")
        UnlockMirrors()
    elif key == 'r':
        print("Retry locking mirrors...")
        RetryLock()
    elif key == 'q':
        print("Exiting...")
    else:
        print(f"Unknown key: {key}")
        return
    print(f"Offset: x={right}, y={up}")
    

def square(cx=DisplaySize[1]//2, cy=DisplaySize[0]//2, size=200):
    """Create a square image with a given center and size."""
    # Create an empty array with the specified size
    global right, up
    img = np.zeros(DisplaySize, dtype='uint32')
    
    # Calculate the coordinates of the square
    start_x = cx - size // 2 + right
    end_x = cx + size // 2 + right
    start_y = cy - size // 2 - up
    end_y = cy + size // 2 - up
    
    # Fill the square area with white color (255, 255, 255)
    img[start_y:end_y, start_x:end_x] = 2**16-1
    
    return img


def StreamFrameBuffer():
    global buf, DisplaySize
    while True:
        # create random noise (16 bit RGB)
        image = square()
        # b = np.random.randint(0x10000,size=DisplaySize,dtype="uint32")
        # push to screen
        buf[:] = image
        time.sleep(0.1)










def make_parallel_mode():
        '''
        Initializes the Raspberry Pi's GPIO lines to communicate with the DLPDLCR230NPEVM,
        and configures the DLPDLCR230NPEVM to project RGB666 parallel video input received from the Raspberry Pi.
        It is recommended to execute this script upon booting the Raspberry Pi.
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
    # Enable screen parallel mode
    print("Initializing parallel mode...")
    make_parallel_mode()
    
    # this turns off the cursor blink:
    os.system ("TERM=linux setterm -foreground black -clear all >/dev/tty0")

    # this is the frambuffer for analog video output - note that this is a 16 bit RGB
    # other setups will likely have a different format and dimensions which you can check with
    # fbset -fb /dev/fb0 
    global buf
    buf = np.memmap('/dev/fb0', dtype='uint32',mode='w+', shape=DisplaySize)

    # fill with white
    buf[:] = 0xffff

    
    # ######## START TASK ########
    
    loop = True
    global stop; stop = False
    global right, up
    right = 0
    up = 0
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
    
    # Listen for keyboard input
    while loop:
        listen_keyboard(on_press=press, until='q')
        loop = False
        
        
    # ######## END TASK ########
    # turn on the cursor again:    
    os.system("TERM=linux setterm -foreground white -clear all >/dev/tty0")
    i2c.terminate()



if __name__ == "__main__": main()