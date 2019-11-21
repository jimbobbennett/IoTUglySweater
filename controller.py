import iotc, os, threading, random
import board
import neopixel
from iotc import IOTConnectType, IOTLogLevel
from random import randint
from dotenv import load_dotenv
load_dotenv()

deviceId = os.environ['DEVICE_ID']
scopeId = os.environ['SCOPE_ID']
deviceKey = os.environ['DEVICE_KEY']

iotc = iotc.Device(scopeId, deviceKey, deviceId, IOTConnectType.IOTC_CONNECT_SYMM_KEY)
iotc.setLogLevel(IOTLogLevel.IOTC_LOGGING_API_ONLY)

pixel_count = 20
pixels = neopixel.NeoPixel(board.D18, pixel_count, auto_write=False, brightness=0.5)

gCanSend = False
gCounter = 0
gMode = 'none'

def onconnect(info):
    global gCanSend
    print("- [onconnect] => status:" + str(info.getStatusCode()))
    if info.getStatusCode() == 0:
       if iotc.isConnected():
         gCanSend = True

def onmessagesent(info):
    print("\t- [onmessagesent] => " + str(info.getPayload()))

def oncommand(info):
    global gMode
    print("- [oncommand] => " + info.getTag() + " => " + str(info.getPayload()))
    gMode = info.getTag()

def onsettingsupdated(info):
    print("- [onsettingsupdated] => " + info.getTag() + " => " + info.getPayload())

def warm_glow_loop():
    print("Warm glow")
    for x in range (0, pixel_count):
        if random.choice([True, False]) == True:
            pixels[x] = (255, 100, 0)
        else:
            pixels[x] = (0, 0, 0)

def colour_flash_loop():
    print("Colour Flash")
    for x in range (0, pixel_count):
        pixels[x] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

def timer_func(stop_timer):
    if gMode == "warm_glow":
        warm_glow_loop()
    elif gMode == "colour_flash":
        colour_flash_loop()
    else:
        print("None")
        pixels.fill((0, 0, 0))

    pixels.show()

    if not stop_timer.is_set():
        threading.Timer(1, timer_func, [stop_timer]).start()

iotc.on("ConnectionStatus", onconnect)
iotc.on("MessageSent", onmessagesent)
iotc.on("Command", oncommand)
iotc.on("SettingsUpdated", onsettingsupdated)

iotc.connect()

stop_timer = threading.Event()
timer_func(stop_timer)

while iotc.isConnected():
    iotc.doNext() # do the async work needed to be done for MQTT
    if gCanSend == True:
        if gCounter % 20 == 0:
            gCounter = 0
            print("Sending state...")
            iotc.sendState("{ \"mode\": \"" + gMode + "\" }")
        gCounter += 1


