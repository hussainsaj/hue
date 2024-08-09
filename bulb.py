#documentations
#https://github.com/studioimaginaire/phue

from phue import Bridge
from datetime import datetime
import time
import json

#based on time, it returns an appropriate brightness and colour temperature
def get_scene():
    #dictionary for all the scenes
    scenes = config['scenes']

    time_slots = config['time_slots']

    now = datetime.now().strftime("%H:%M")

    sorted_times = sorted(time_slots.keys())

    #default value, last scene in the list
    scene = time_slots[sorted_times[-1]]

    #finds the current scene
    for i in range(len(sorted_times)):
        if now < sorted_times[i]:
            scene = time_slots[sorted_times[i-1]]
            break

    return scenes[scene]

#updates the bulb state
def update_bulb(bulb_id, scene):
    command =  {
        'on' : True,
        'bri' : scene['brightness'],
        'ct' : scene['colour_temperature']
    }

    b.set_light(bulb_id, command)

    return

#checks for any changes for each bulb
def check_update(bulbs):
    current_status = b.get_api()
    new_scene = get_scene()

    #update each bulb in the list
    for i in range(len(bulbs)):
        bulb = bulbs[i]

        current_state = current_status['lights'][str(bulb['id'])]['state']['reachable']

        #only update if the time based scene has changed or the bulb has turned on
        if (current_state == True and (current_state != bulb['previous_state'] or new_scene != bulb['previous_scene'])):
            update_bulb(bulb['id'], new_scene)
            bulb['state_tick'] += 1

            #updates the bulb 5 times to ensure that it worked
            if (bulb['state_tick'] > 5):
                bulb['state_tick'] = 0
                bulb['previous_state'] = current_state
                bulb['previous_scene'] = new_scene

                print (current_status['lights'][str(bulb['id'])]['name'], new_scene)

        #if the bulb has turned off
        elif (current_state == False and current_state != bulb['previous_state']):
            bulb['previous_state'] = current_state
            bulb['previous_scene'] = new_scene

        bulbs[i] = bulb
    
    return bulbs

#load config
with open('config.json') as file:
    config = json.load(file)

bulbs = config['bulbs']

for i in range(len(bulbs)):
    bulbs[i] = {
        'id': bulbs[i],
        'state_tick': 0,
        'previous_state': None,
        'previous_scene': None
    }

#connect to the bridge
b = Bridge(config['ip_address'])
b.connect()

heartbeat_counter = 0

while True:
    time.sleep(1)

    try:
        bulbs = check_update(bulbs)
    except Exception as e:
        print(f"Error checking bulb: {str(e)}")

    heartbeat_counter += 1
    if heartbeat_counter >= 60:
        print('heartbeat', datetime.now())
        heartbeat_counter = 0

#https://github.com/studioimaginaire/phue
#button guide
#https://www.hackster.io/robin-cole/hijack-a-hue-remote-to-control-anything-with-home-assistant-5239a4

#next update
#transistions