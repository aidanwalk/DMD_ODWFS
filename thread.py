"""
This script is not integrated into test.py as it requires streaming
to the framebuffer of the Raspberry Pi, then the Raspberry Pi 
transmits this to the EVM .

Streaming to the Raspberry Pi Frame Buffer from Quasimondo 2025-06-19
https://gist.github.com/Quasimondo/e47a5be0c2fa9a3ef80c433e3ee2aead
"""

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

from sshkeyboard import listen_keyboard, stop_listening

# ===============================================================================
# GLOBAL VARIABLES -- CHANGE ME
# ===============================================================================
# Set the display size to match your framebuffer resolution
# This must match resolution listed from:
#     $ fbset -fb /dev/fb0
# "geometry"
global DisplaySize; DisplaySize = (1080, 1920)
global step; step=250
global sq_size; sq_size=500
# ===============================================================================


class Set(Enum):
    Disabled = 0
    Enabled = 1



def LockMirrors():
    '''
    Locks the mirrors on the DLPDLCR230NPEVM.
    This is useful for freezing the DMD mirrors.
    '''
    global locked
    print("Locking mirrors.")
    Summary = WriteMirrorLock(MirrorLockOptions.DmdInterfaceLock)
    locked = True
    return Summary


def RetryLock():
    '''
    Retries to lock the mirrors on the DMD. 
    Often times you may get unlucky and lock the mirrors on the wrong side of 
    the duty cycle. 
    
    Quickly unlocks the mirros and then locks them again.
    '''
    global locked
    if not locked:
        print("The mirrors were not locked. Locking.")
        LockMirrors()
    
    else:
        UnlockMirrors()
        time.sleep(0.25)
        Summary = LockMirrors()
        return Summary


def UnlockMirrors():
    '''
    Unlocks the mirrors on the DLPDLCR230NPEVM.
    This is useful for unfreezing the DMD mirrors.
    '''
    global locked
    print("Unlocking mirrors.")
    Summary = WriteMirrorLock(MirrorLockOptions.DmdInterfaceUnlock)
    locked = False
    return Summary


def Menu():
    menu = """
------------------------------
             MENU                
------------------------------
 right  Move Right
 left   Move Left             
 up     Move Up
 down   Move Down
 l      Lock Mirrors
 r      Retry Lock
 u      Unlock Mirrors
 m      Display Menu                          
------------------------------
    """
    print(menu)
    return None


def MoveUp():
    global up
    up += step
    print(f"Offset: x={right}, y={up}")
    return None

def MoveDown():
    global up
    up -= step
    print(f"Offset: x={right}, y={up}")
    return None

def MoveRight():
    global right
    right += step
    print(f"Offset: x={right}, y={up}")
    return None

def MoveLeft():
    global right
    right -= step
    print(f"Offset: x={right}, y={up}")
    return None

def Quit():
    stop_listening()
    print("Exiting...")
    return None



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
    

def square(cx=DisplaySize[1]//2, cy=DisplaySize[0]//2, size=sq_size):
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
    img[start_y:end_y, start_x:end_x] = 0xffffffff #2**32-1
    
    return img


def StreamFrameBuffer():
    global buf, DisplaySize
    while True:
        # create a 32 bit image
        image = square()
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
    global mode 
    # Available modes for the DLPDLCR230NPEVM
    # Each mode corresponds to a function that changes the display.
    # The keys are the characters that the user can input to select the mode.
    # The values are the functions that will be called when the user selects the mode.
    mode = {
        'up'    : MoveUp, 
        'down'  : MoveDown,
        'left'  : MoveLeft,
        'right' : MoveRight,
        'l'     : LockMirrors,
        'r'     : RetryLock,
        'u'     : UnlockMirrors,
        'q'     : Quit,
        'm'     : Menu,
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
    
    Menu()
    # Listen for keyboard input
    while loop:
        listen_keyboard(on_press=Call)
        loop = False
        
    
    # ######## END TASK ########
    UnlockMirrors()
    sq_size = 0
    time.sleep(0.5)
    buf[:] = 0x00000000
    # turn on the cursor again:    
    os.system("TERM=linux setterm -foreground white -clear all >/dev/tty0")
    i2c.terminate()



if __name__ == "__main__": main()