# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
import uos, machine
#uos.dupterm(None, 1) # disable REPL on UART(0)
import gc
#import webrepl
#webrepl.start()
gc.collect()

from machine import Pin, I2C, Timer
import sh1106
import json
import time
import urequests as requests
import uasyncio as asyncio

ssid = '<WiFi>' # name of your WiFi
psk = '<Password>' # password of your WiFi
active_delay = 5 # delay to refresh data while active (in seconds)
idle_delay  = 60 # delay to refresh data while idle (in seconds)
grill_addresses = {'http://10.0.0.40/api/current'} #example with only one grill
#grill_addresses = {'http://10.0.0.40/api/current', 'http://10.0.0.41/api/current'} #example of multiple grills
display_scroll_rate = 3 # how many lines to scroll every second

#probably don't change these, but small changes will be okay
box_width = 28
box_height = 25
box_spacing = 1

screen_width = 128
screen_height = 64

cache = {}

i2c = I2C(scl=Pin(5), sda=Pin(4), freq=400000)
display = sh1106.SH1106_I2C(screen_width, screen_height, i2c, Pin(16), 0x3c, 180)
display.sleep(False)
display.fill(0)
#display.text('Testing 1', 0, 0, 1)
#display.show()

import network
ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)
sta_if = network.WLAN(network.STA_IF)
#sta_if.ifconfig(("<static IP>", "255.255.255.0", "<router IP>", "<router IP>")) #uncomment and configure if you want/need a static IP address
if not sta_if.isconnected():
    display.text('Connecting to', 1, 0)
    display.text(ssid, 1, 10)
    display.show()
    sta_if.active(True)
    sta_if.connect(ssid, psk)
    i = 0
    while not sta_if.isconnected():
        time.sleep_ms(500)
        display.pixel(1+(i*3), 18, 1)
        display.show()
        i += 1
        pass
display.text('Connected!', 1, 24)
display.show()
steps = 4
print('network config:', sta_if.ifconfig())
for y in range(0, int(screen_height/2), steps):
    display.scroll(0,0-steps)
    # for line in range(0,steps):
    #     display.line(0,line,screen_width,line,0)
    display.show()
    time.sleep_ms(250)
display.text('Refreshing', (screen_width/2)-(len('Refreshing')/2)*4, 0)
display.show()