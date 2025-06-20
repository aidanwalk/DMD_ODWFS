# Controller for DMD DLP230NP .23 1080p.

This code was developed to enable low-level control the DLPDLCR230NPEVM DMD
using a Raspberry Pi.

It allows the user to interact with the DMD (Digital Micromirror Device) to 
display various patterns on the fly. It enables critial functions for bench 
testing such as mirror locking, turning all mirrors ON or OFF, and displaying
various patterns such as checkerboard, horizontal ramp, and vertical ramp.
It also provides a simple menu interface for user interaction.

It is recommended to run the script test.py on boot.

### Raspberry Pi Setup
Before using this code, the Raspberry Pi must be set up for communication with 
the EVM. Detailed instructions are provided by TI. Please refer to this guide
(see section 9) [User's Guide  DLP® LightCrafterTM Display 230NP EVM](https://www.ti.com/lit/ug/dlpu103b/dlpu103b.pdf?ts=1750080331467&ref_url=https%253A%252F%252Fwww.ti.com%252Ftool%252FDLPDLCR230NPEVM)
for setting up the Raspberry Pi


### Controlling the DMD
The main script for DMD testing is test.py.

To control the DMD, run: <br />
\$ python test.py

On Startup, this will display a menu of DMD command options. Enter 'm' at any 
time to view this menu again. 
```
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
```


## REFERENCES

### Raspberry Pi Setup
The Raspberri Pi must be set up according to this TI User's Guide: <br />
[User's Guide  DLP® LightCrafterTM Display 230NP EVM](https://www.ti.com/lit/ug/dlpu103b/dlpu103b.pdf?ts=1750080331467&ref_url=https%253A%252F%252Fwww.ti.com%252Ftool%252FDLPDLCR230NPEVM) (see section 9) <br />


### TI API
For more information on the API developed by TI, see TI Software Programmer's
Guide: <br /> [DLPC3436, DLPC3426 Software Programmer's Guide](https://www.ti.com/lit/ug/dlpu078a/dlpu078a.pdf?ts=1750130382911) <br />

The API can be downloaded from the [TI website](https://www.ti.com/tool/DLPDLCR230NPEVM).