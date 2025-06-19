# Controller for DMD DLP230NP .23 1080p.

This code was developed to enable low-level control the DLPDLCR230NPEVM DMD
using a Raspberry Pi.

It allows the user to interact with the DMD (Digital Micromirror Device) to 
display various patterns on the fly. It enables critial functions for bench 
testing such as mirror locking, turning all mirrors ON or OFF, and displaying
various patterns such as checkerboard, horizontal ramp, and vertical ramp.
It also provides a simple menu interface for user interaction.

It is recommended to run the script test.py on boot.

## 1. Setup the Raspberri Pi for communication with the EVM


## 2. Run test.py
To control the DMD, run:
/$ python test.py


## REFERENCES

### Raspberry Pi Setup
The Raspberri Pi must be set up according to this TI User's Guide:
"User's Guide  DLP® LightCrafterTM Display 230NP EVM" (see section 9)
https://www.ti.com/lit/ug/dlpu103b/dlpu103b.pdf?ts=1750080331467&ref_url=https%253A%252F%252Fwww.ti.com%252Ftool%252FDLPDLCR230NPEVM

### TI API
For more information on the API developed by TI, see TI Software Programmer's
Guide: "DLPC3436, DLPC3426 Software Programmer's Guide"
https://www.ti.com/lit/ug/dlpu078a/dlpu078a.pdf?ts=1750130382911

The API can be downloaded from the TI website:
https://www.ti.com/tool/DLPDLCR230NPEVM