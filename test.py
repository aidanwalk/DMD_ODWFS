"""
This script is developed to enable low-level control the DLPDLCR230NPEVM DMD
using a Raspberry Pi.

It allows the user to interact with the DMD (Digital Micromirror Device) to 
display various patterns on the fly. It enables critial functions for bench 
testing such as mirror locking, turning all mirrors ON or OFF, and displaying
various patterns such as checkerboard, horizontal ramp, and vertical ramp.
It also provides a simple menu interface for user interaction.

It is recommended to run this script on boot.


-------------------------------------------------------------------------------
REFERENCES
-------------------------------------------------------------------------------
The Raspberri Pi must be set up according to the TI User's Guide 
(see section 9):
"User's Guide  DLP® LightCrafterTM Display 230NP EVM"
https://www.ti.com/lit/ug/dlpu103b/dlpu103b.pdf?ts=1750080331467&ref_url=https%253A%252F%252Fwww.ti.com%252Ftool%252FDLPDLCR230NPEVM


For more information on the API, see TI Sotware Programmer's Guide:
"DLPC3436, DLPC3426 Software Programmer's Guide"
https://www.ti.com/lit/ug/dlpu078a/dlpu078a.pdf?ts=1750130382911


API can be downloaded from the TI website:
https://www.ti.com/tool/DLPDLCR230NPEVM



@author: Aidan Walk
date: 2025-06-19
"""


import time
from enum import Enum

import sys, os.path
python_dir = (os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(python_dir)
from api.dlpc343x_xpr4 import *
from api.dlpc343x_xpr4_evm import *
from linuxi2c import *
import i2c

from sshkeyboard import listen_keyboard, stop_listening



def DisplayWhite():
    """
    Turns all DMD mirrors to the 'ON' position. 
    """
    print("Setting all mirrors to ON position (white).")
    Summary = WriteFpgaTestPatternSelect(Set.Disabled,  
                                         FpgaTestPatternColor.White,
                                         FpgaTestPattern.SolidField,  
                                         255)
    return Summary


def DisplayBlack():
    """
    Turns all DMD mirrors to the 'OFF' position. 
    """
    print("Setting all mirrors to OFF position (black).")
    Summary = WriteFpgaTestPatternSelect(Set.Disabled,  
                                         FpgaTestPatternColor.Black,
                                         FpgaTestPattern.SolidField,  
                                         255)
    return Summary


def DisplayCheckerboard():
    '''
    Displays a checkerboard pattern on the DMD.
    '''
    print("Displaying checkerboard pattern.")
    Summary = WriteFpgaTestPatternSelect(Set.Disabled,  
                                         FpgaTestPatternColor.White,   
                                         FpgaTestPattern.Checkerboard,  
                                         50)
    return Summary


def DisplayHorizontalRamp():
    '''
    Displays a horizontal ramp pattern on the DMD.
    The ramp goes from black to white.
    '''
    print("Displaying horizontal ramp pattern.")
    Summary = WriteFpgaTestPatternSelect(Set.Disabled,  
                                         FpgaTestPatternColor.White,   
                                         FpgaTestPattern.HorizontalRamp,  
                                         255)
    return Summary


def DisplayVerticalRamp():
    '''
    Displays a vertical ramp pattern on the DMD.
    The ramp goes from black to white.
    '''
    print("Displaying vertical ramp pattern.")
    Summary = WriteFpgaTestPatternSelect(Set.Disabled,  
                                         FpgaTestPatternColor.White,   
                                         FpgaTestPattern.VerticalRamp,  
                                         255)
    return Summary


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


def Quit():
    """
    Exits the program.
    """
    stop_listening()
    print("Exiting...")
    global locked
    if locked:
        UnlockMirrors()
    DisplayBlack()
    global run
    run = False
    return run


def Menu():
    print()
    menu = """
------------------------------
             MENU                
------------------------------
   w    White             
   b    Black        
   c    Checkerboard      
   h    Horizontal Ramp   
   v    Vertical Ramp     
   l    Lock Mirrors              
   r    Retry Lock
   u    Unlock Mirrors            
   q    Quit                      
   m    Display Menu               
------------------------------
    """
    print(menu)
    return None


def Call(name):
    """
    Calls the function associated with the name.
    """
    global locked
    chars_to_check = 'uqrm'
    # If we are not unlocking the mirrors or quitting,
    # check if the mirrors are locked. 
    # If they are locked, we cannot change the display.
    if not any(char in name for char in chars_to_check) and locked: 
        print("Mirrors are locked. Please unlock them first.")
        return None
    
    # Otherwise, change the display if a valid option is selected
    if name not in mode:
        print("Invalid option. Please try again.")
        return Menu()

    func = mode[name]
    return func()
        
        


# Available modes for the DLPDLCR230NPEVM
# Each mode corresponds to a function that changes the display.
# The keys are the characters that the user can input to select the mode.
# The values are the functions that will be called when the user selects the mode.
mode = {
    'w' : DisplayWhite, 
    'b' : DisplayBlack,
    'c' : DisplayCheckerboard, 
    'h' : DisplayHorizontalRamp, 
    'v' : DisplayVerticalRamp,
    'l' : LockMirrors, 
    'r' : RetryLock,
    'u' : UnlockMirrors,
    'q' : Quit, 
    'm' : Menu,
}


class Set(Enum):
    Disabled = 0
    Enabled = 1


def main():
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
        # Start with a clean slate
        Summary = WriteDisplayImageCurtain(1,Color.Black)
        Summary = WriteFpgaTestPatternSelect(Set.Disabled,  FpgaTestPatternColor.Black,   FpgaTestPattern.SolidField,  0)
        Summary = WriteSourceSelect(Source.FpgaTestPattern, Set.Disabled)
        # Set the input image size to the DMD size (it is possible to input an
        # image 1920x1080 pixels, which then means a single mirror displays 
        # four pixels. Lets dumb down the DMD as much as possible, though.)
        Summary = WriteInputImageSize(960, 540)
        Summary = WriteDisplayImageCurtain(0,Color.Black)
        
        
        
        global run; run = True
        global locked; locked = False
        max_loop = 100_000
        loop = 0
        Menu()
        while run and (loop < max_loop):
            listen_keyboard(on_press=Call, 
                            delay_second_char=0.1,
                            delay_other_chars=0.05,)
            loop+=1

        
        # ##### ##### Command call(s) end here ##### #####
        i2c.terminate()


if __name__ == "__main__" : main()