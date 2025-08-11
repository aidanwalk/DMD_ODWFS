
import sys, os.path
python_dir = (os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(python_dir)
from api.dlpc343x_xpr4 import *
from api.dlpc343x_xpr4_evm import *
from linuxi2c import *
import i2c


class Set(Enum):
    Disabled = 0
    Enabled = 1
    


def make_parallel_mode():
    '''
    Initializes the Raspberry Pi's GPIO lines to communicate with the DLPDLCR230NPEVM,
    and configures the DLPDLCR2OA30NPEVM to project RGB666 parallel video input received from the Raspberry Pi.
    '''

    gpio_init_enable = True          # Set to FALSE to disable default initialization of Raspberry Pi GPIO pinouts. TRUE by default.
    i2c_time_delay_enable = False    # Set to FALSE to prevent I2C commands from waiting. May lead to I2C bus hangups with some commands if FALSE.
    i2c_time_delay = 1             # Lowering this value will speed up I2C commands. Too small delay may lead to I2C bus hangups with some commands.
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
    Summary = WriteDelay(100)
    time.sleep(1)
    Summary = WriteDisplayImageCurtain(0,Color.Black)
    
    return
