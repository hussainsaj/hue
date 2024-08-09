from phue import Bridge
from datetime import datetime

import time

b = Bridge('192.168.1.2')

b.connect()

#toggles the bulb and sets the appropriate brightness based on time
def powerButtonPressed():
    state = b.get_light(bulb,'on')

    if (state):
        b.set_light(bulb,'on', False)
    else:
        now = datetime.now()

        morning = now.replace(hour=7, minute=0, second=0, microsecond=0)
        evening = now.replace(hour=20, minute=0, second=0, microsecond=0)
        night = now.replace(hour=23, minute=0, second=0, microsecond=0)

        #default brightness for midnight
        brightness = 1

        #brightness for morning and evening
        if (now >= morning and now < evening):
            brightness = 254
        elif (now >= evening and now < night):
            brightness = 145

        #set the lights
        b.set_light(bulb,'on', True)
        b.set_light(bulb, 'bri', brightness)


#increase brightness by 20%
def brightnessUpPressed():
    #check if the light is on
    if(b.get_light(bulb,'on')):
        #calculate new brightness
        newBrightness = b.get_light(bulb, 'bri') + 50
        
        #brightness can't exceed 254
        if (newBrightness > 254):
            newBrightness = 254
        
        b.set_light(bulb, 'bri', newBrightness)


#decrease brightness by 20%
def brightnessDownPressed():
    #check if the light is on
    if(b.get_light(bulb,'on')):
        #calculate new brightness
        newBrightness = b.get_light(bulb, 'bri') - 50
        
        #brightness can't get lower than 1
        if (newBrightness < 1):
            newBrightness = 1
        
        b.set_light(bulb, 'bri', newBrightness)


#toggles between three brightness presets
def hueButtonPressed():
    #preset brightness levels
    high = 254
    mid = 145
    low = 1

    currentBrightness = b.get_light(bulb, 'bri')

    #set the next brightness level
    if(currentBrightness == high):
        newBrightness = low
    elif (currentBrightness < high and currentBrightness >= mid):
        newBrightness = high
    elif (currentBrightness < mid and currentBrightness >= low):
        newBrightness = mid
    
    b.set_light(bulb, 'bri', newBrightness)

#test = b.get_api()['lights']['7']['state']

bulb = 7

#powerButtonPressed()
#brightnessUpPressed()
#brightnessDownPressed()
#hueButtonPressed()