# //*****************************************************************************
# * | File        :	  epd2in13.py
# * | Author      :   Waveshare team
# * | Function    :   Electronic paper driver
# * | Info        :
# *----------------
# * |	This version:   V3.0
# * | Date        :   2018-11-01
# * | Info        :   python2 demo
# * 1.Remove:
#   digital_write(self, pin, value)
#   digital_read(self, pin)
#   delay_ms(self, delaytime)
#   set_lut(self, lut)
#   self.lut = self.lut_full_update
# * 2.Change:
#   display_frame -> TurnOnDisplay
#   set_memory_area -> SetWindow
#   set_memory_pointer -> SetCursor
# * 3.How to use
#   epd = epd2in13.EPD()
#   epd.init(epd.lut_full_update)
#   image = Image.new('1', (epd2in13.EPD_WIDTH, epd2in13.EPD_HEIGHT), 255)
#   ...
#   drawing ......
#   ...
#   epd.display(getbuffer(image))
# ******************************************************************************//
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and//or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import time
import spidev
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw

# Pin definition
RST_PIN = 17
DC_PIN = 25
CS_PIN = 8
BUSY_PIN = 24

# SPI device, bus = 0, device = 0
SPI = spidev.SpiDev(0, 0)


def digital_write(pin, value):
    GPIO.output(pin, value)


def digital_read(pin):
    return GPIO.input(BUSY_PIN)


def delay_ms(delaytime):
    time.sleep(delaytime / 1000.0)


def spi_writebyte(data):
    SPI.writebytes(data)


def module_init():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(RST_PIN, GPIO.OUT)
    GPIO.setup(DC_PIN, GPIO.OUT)
    GPIO.setup(CS_PIN, GPIO.OUT)
    GPIO.setup(BUSY_PIN, GPIO.IN)
    SPI.max_speed_hz = 2000000
    SPI.mode = 0b00
    return 0;


# Display resolution
EPD_WIDTH = 128
EPD_HEIGHT = 250

# EPD2IN13 commands
DRIVER_OUTPUT_CONTROL                       = 0x01
BOOSTER_SOFT_START_CONTROL                  = 0x0C
GATE_SCAN_START_POSITION                    = 0x0F
DEEP_SLEEP_MODE                             = 0x10
DATA_ENTRY_MODE_SETTING                     = 0x11
SW_RESET                                    = 0x12
TEMPERATURE_SENSOR_CONTROL                  = 0x1A
MASTER_ACTIVATION                           = 0x20
DISPLAY_UPDATE_CONTROL_1                    = 0x21
DISPLAY_UPDATE_CONTROL_2                    = 0x22
WRITE_RAM                                   = 0x24
WRITE_VCOM_REGISTER                         = 0x2C
WRITE_LUT_REGISTER                          = 0x32
SET_DUMMY_LINE_PERIOD                       = 0x3A
SET_GATE_TIME                               = 0x3B
BORDER_WAVEFORM_CONTROL                     = 0x3C
SET_RAM_X_ADDRESS_START_END_POSITION        = 0x44
SET_RAM_Y_ADDRESS_START_END_POSITION        = 0x45
SET_RAM_X_ADDRESS_COUNTER                   = 0x4E
SET_RAM_Y_ADDRESS_COUNTER                   = 0x4F
TERMINATE_FRAME_READ_WRITE                  = 0xFF

class EPD:
    def __init__(self):
        self.reset_pin = RST_PIN
        self.dc_pin = DC_PIN
        self.busy_pin = BUSY_PIN
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT

    FULL_UPDATE = 0
    PART_UPDATE = 1

    lut_full_update = [
        0x22, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x11,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x1E, 0x1E, 0x1E, 0x1E, 0x1E, 0x1E, 0x1E, 0x1E,
        0x01, 0x00, 0x00, 0x00, 0x00, 0x00
    ]

    lut_partial_update  = [
        0x18, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x0F, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    ]

    # Hardware reset
    def reset(self):
        digital_write(self.reset_pin, GPIO.HIGH)
        delay_ms(200)
        digital_write(self.reset_pin, GPIO.LOW)  # module reset
        delay_ms(200)
        digital_write(self.reset_pin, GPIO.HIGH)
        delay_ms(200)

    def send_command(self, command):
        digital_write(self.dc_pin, GPIO.LOW)
        spi_writebyte([command])

    def send_data(self, data):
        digital_write(self.dc_pin, GPIO.HIGH)
        spi_writebyte([data])

    def wait_until_idle(self):
        while (digital_read(self.busy_pin) == 1):  # 0: idle, 1: busy
            delay_ms(100)

    def TurnOnDisplay(self):
        self.send_command(0x22)
        self.send_data(0xC7)
        self.send_command(0x20)
        self.wait_until_idle()

##
 #  @brief: set the look-up table register
 ##
    def set_lut(self, lut):
        self.lut = lut
        self.send_command(WRITE_LUT_REGISTER)
        # the length of look-up table is 30 bytes
        for i in range(0, len(lut)):
            self.send_data(self.lut[i])

    def init(self, update):
        if (module_init() != 0):
            return -1
        # EPD hardware init start
        self.reset()
        self.wait_until_idle()
        if (update == self.FULL_UPDATE):
            self.lut = self.lut_full_update
            self.send_command(0x12)  # soft reset
            self.wait_until_idle()
            self.send_command(DRIVER_OUTPUT_CONTROL)
            self.send_data((EPD_HEIGHT - 1) & 0xFF)
            self.send_data(((EPD_HEIGHT - 1) >> 8) & 0xFF)
            self.send_data(0x00)                     # GD = 0 SM = 0 TB = 0
            self.send_command(BOOSTER_SOFT_START_CONTROL)
            self.send_data(0xD7)
            self.send_data(0xD6)
            self.send_data(0x9D)
#            self.send_command(WRITE_VCOM_REGISTER)
#            self.send_data(0x9B)                     # VCOM 7C
            self.send_command(SET_DUMMY_LINE_PERIOD)
            self.send_data(0x1A)                     # 4 dummy lines per gate
            self.send_command(SET_GATE_TIME)
            self.send_data(0x08)                     # 2us per line
            self.send_command(DATA_ENTRY_MODE_SETTING)
            self.send_data(0x03)                     # X increment Y increment
            self.send_command(0x44)  # set Ram-X address start//end position
            self.send_data(0x00)
            self.send_data(0x0F)  # 0x0C-->(15+1)*8=128

            self.send_command(0x45)  # set Ram-Y address start//end position
            self.send_data(0xF9)  # 0xF9-->(249+1)=250
            self.send_data(0x00)
            self.send_data(0x00)
            self.send_data(0x00)

            self.send_command(0x3C)  # BorderWavefrom
            self.send_data(0x03)

            self.send_command(0x2C)  # VCOM Voltage
            self.send_data(0x55)  #
            self.set_lut(self.lut)
            self.send_command(0x4E)  # set RAM x address count to 0
            self.send_data(0x00)
            self.send_command(0x4F)  # set RAM y address count to 0X127
            self.send_data(0xF9)
            self.send_data(0x00)
            self.wait_until_idle()
        else:
            self.lut = self.lut_partial_update
            self.send_command(0x2C)  # VCOM Voltage
            self.send_data(0x26)
            self.wait_until_idle()
            self.set_lut(self.lut)
            self.send_command(0x22)
            self.send_data(0xC0)
            self.send_command(0x20)
            self.wait_until_idle()
            self.send_command(0x3C)  # BorderWavefrom
            self.send_data(0x01)


        return 0

##
 #  @brief: specify the memory area for data R/W
 ##
    def set_memory_area(self, x_start, y_start, x_end, y_end):
        self.send_command(SET_RAM_X_ADDRESS_START_END_POSITION)
        # x point must be the multiple of 8 or the last 3 bits will be ignored
        self.send_data((x_start >> 3) & 0xFF)
        self.send_data((x_end >> 3) & 0xFF)
        self.send_command(SET_RAM_Y_ADDRESS_START_END_POSITION)
        self.send_data(y_start & 0xFF)
        self.send_data((y_start >> 8) & 0xFF)
        self.send_data(y_end & 0xFF)
        self.send_data((y_end >> 8) & 0xFF)

##
 #  @brief: specify the start point for data R/W
 ##
    def set_memory_pointer(self, x, y):
        self.send_command(SET_RAM_X_ADDRESS_COUNTER)
        # x point must be the multiple of 8 or the last 3 bits will be ignored
        self.send_data((x >> 3) & 0xFF)
        self.send_command(SET_RAM_Y_ADDRESS_COUNTER)
        self.send_data(y & 0xFF)
        self.send_data((y >> 8) & 0xFF)
        self.wait_until_idle()

    def getbuffer(self, image):
        if self.width % 8 == 0:
            linewidth = self.width // 8
        else:
            linewidth = self.width // 8 + 1

        buf = [0xFF] * (linewidth * self.height)
        image_monocolor = image.convert('1')
        imwidth, imheight = image_monocolor.size
        pixels = image_monocolor.load()

        if (imwidth == self.width and imheight == self.height):
            # print("Vertical")
            for y in range(imheight):
                for x in range(imwidth):
                    if pixels[x, y] == 0:
                        x = imwidth - x
                        buf[x // 8 + y * linewidth] &= ~(0x80 >> (x % 8))
        elif (imwidth == self.height and imheight == self.width):
            # print("Horizontal")
            for y in range(imheight):
                for x in range(imwidth):
                    newx = y
                    newy = self.height - x - 1
                    if pixels[x, y] == 0:
                        newy = imwidth - newy - 1
                        buf[newx // 8 + newy * linewidth] &= ~(0x80 >> (y % 8))
        return buf

##
 #  @brief: put an image to the frame memory.
 #          this won't update the display.
 ##
    def set_frame_memory(self, image, x, y):
        if (image == None or x < 0 or y < 0):
            return
        image_monocolor = image.convert('1')
        image_width, image_height  = image_monocolor.size
        # x point must be the multiple of 8 or the last 3 bits will be ignored
        x = x & 0xF8
        image_width = image_width & 0xF8
        if (x + image_width >= self.width):
            x_end = self.width - 1
        else:
            x_end = x + image_width - 1
        if (y + image_height >= self.height):
            y_end = self.height - 1
        else:
            y_end = y + image_height - 1
        self.set_memory_area(x, y, x_end, y_end)
        # send the image data
        pixels = image_monocolor.load()
        byte_to_send = 0x00
        for j in range(y, y_end + 1):
            self.set_memory_pointer(x, j)
            self.send_command(WRITE_RAM)
            # 1 byte = 8 pixels, steps of i = 8
            for i in range(x, x_end + 1):
                # Set the bits for the column of pixels at the current position.
                if pixels[i - x, j - y] != 0:
                    byte_to_send |= 0x80 >> (i % 8)
                if (i % 8 == 7):
                    self.send_data(byte_to_send)
                    byte_to_send = 0x00

##
 #  @brief: clear the frame memory with the specified color.
 #          this won't update the display.
 ##
    def clear_frame_memory(self, color):
        self.set_memory_area(0, 0, self.width - 1, self.height - 1)
        self.set_memory_pointer(0, 0)
        self.send_command(WRITE_RAM)
        # send the color data
        for i in range(0, int(self.width / 8 * self.height)):
            self.send_data(color)


    def display(self, image):
        self.clear_frame_memory(0xFF)
        self.set_frame_memory(image, 0, 0)
        self.TurnOnDisplay()

    def displayPartial(self, image):
        self.clear_frame_memory(0xFF)
        self.set_frame_memory(image, 0, 0)
        self.TurnOnDisplay()

    def Clear(self, color):
        if self.width % 8 == 0:
            linewidth = self.width // 8
        else:
            linewidth = self.width // 8 + 1
        # print(linewidth)

        self.send_command(0x24)
        for j in range(0, self.height):
            for i in range(0, linewidth):
                self.send_data(color)
        self.TurnOnDisplay()

    def Wipe(self, color):
        step = 16
        x = 0
        f = True 
        while(f):
            bimage = Image.new('1', (self.width, self.height), 255)  # 255: clear the frame
            bdraw = ImageDraw.Draw(bimage)
            bdraw.rectangle((x, 0, step+x-1, self.height-1), fill = 0)
            self.clear_frame_memory(0xFF)
            self.set_frame_memory(bimage, 0, 0)
            self.TurnOnDisplay()
            bimage = Image.new('1', (self.width, self.height), 255)  # 255: clear the frame
            bdraw = ImageDraw.Draw(bimage)
            bdraw.rectangle((x, 0, step+x-1, self.height-1), fill = 0)
            self.clear_frame_memory(0xFF)
            self.set_frame_memory(bimage, 0, 0)
            self.TurnOnDisplay()
            x += step
            f = (x <= self.width)



    def sleep(self):
        self.send_command(0x22)  # POWER OFF
        self.send_data(0xC3)
        self.send_command(0x20)

        self.send_command(0x10)  # enter deep sleep
        self.send_data(0x01)
        delay_ms(100)

    ### END OF FILE ###
