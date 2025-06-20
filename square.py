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

import numpy as np
import os
import time
from sshkeyboard import listen_keyboard

import init_parallel_mode

global DisplaySize; DisplaySize = (984, 1824)  # Set the display size to match your framebuffer resolution

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
    try:
        while True:
            # create random noise (16 bit RGB)
            image = square()
            # b = np.random.randint(0x10000,size=DisplaySize,dtype="uint32")
            # push to screen
            buf[:] = image
            time.sleep(0.1)

    except KeyboardInterrupt:
        pass
    return




def main():
    # Enable screen parallel mode
    init_parallel_mode.main()
    # this turns off the cursor blink:
    os.system ("TERM=linux setterm -foreground black -clear all >/dev/tty0")

    # this is the frambuffer for analog video output - note that this is a 16 bit RGB
    # other setups will likely have a different format and dimensions which you can check with
    # fbset -fb /dev/fb0 
    global buf
    buf = np.memmap('/dev/fb0', dtype='uint32',mode='w+', shape=DisplaySize)

    # fill with white
    buf[:] = 0xffff

    loop = True
    global stop; stop = False
    global right, up
    right = 0
    up = 0

    while loop:
        print("Press Ctrl-C to stop")
        StreamFrameBuffer()
        ans = input('Continue? (y/n), move? (m): ')
        if ans == 'm':
            print("Press arrow keys to move the square, 'q' to quit")
            listen_keyboard(on_press=press, until='q')
            continue
        if ans.lower() != 'y':
            loop = False


    # turn on the cursor again:    
    os.system("TERM=linux setterm -foreground white -clear all >/dev/tty0")



if __name__ == "__main__": main()