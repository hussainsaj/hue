#documentations
#https://github.com/studioimaginaire/phue

from phue import Bridge
from datetime import datetime
import time
import json
import math

#based on time, it returns an appropriate brightness and colour temperature
def get_scene(bulb_group):
    #function to calculate the time difference
    def calculate_time_difference(time1, time2):
        time_format = "%H:%M"

        # Convert the time strings to datetime objects
        time1 = datetime.strptime(time1, time_format)
        time2 = datetime.strptime(time2, time_format)

        # Calculate the difference in minutes
        difference = time2 - time1
        difference_in_minutes = int(difference.total_seconds() / 60)

        return abs(difference_in_minutes)

    #creates a new scene
    def calculate_scene(difference, current_scene, next_scene):
        new_scene = {}
        interpolation_factor = difference / config['transistion_period']

        for key in current_scene:    
            # Interpolate the value for each key
            current_value = current_scene[key]
            next_value = next_scene[key]
            new_value = next_value + ((current_value - next_value) * interpolation_factor)
            
            # Assign the new value to the new_scene
            new_scene[key] = math.floor(new_value)

        return new_scene

    #dictionary for all the scenes
    scenes = config['scenes']

    time_slots = config['time_slot_groups'][bulb_group]

    now = datetime.now().strftime("%H:%M")

    sorted_times = sorted(time_slots.keys())

    #default value, last scene in the list
    new_scene = scenes[time_slots[sorted_times[-1]]]

    #finds the current scene
    for i in range(len(sorted_times)):
        if now < sorted_times[i]:
            difference = calculate_time_difference(now, sorted_times[i])

            #Calculate transition if within transition period
            if difference <= config['transistion_period']:
                new_scene = calculate_scene(difference, scenes[time_slots[sorted_times[i-1]]], scenes[time_slots[sorted_times[i]]])
            else:
                new_scene = scenes[time_slots[sorted_times[i-1]]]

            break

    return new_scene

#updates the bulb state
def update_bulb(bulb_id, scene):
    b.set_light(bulb_id, scene)
    b.set_light(bulb_id,'on', True)

    return

#checks for any changes for each bulb
def check_update(bulbs):
    current_status = b.get_api()

    #update each bulb in the list
    for i in range(len(bulbs)):
        bulb = bulbs[i]

        new_scene = get_scene(bulbs[i]['group'])

        current_state = current_status['lights'][str(bulb['id'])]['state']['reachable']

        #only update if the time based scene has changed or the bulb has turned on
        if (current_state == True and (current_state != bulb['previous_state'] or new_scene != bulb['previous_scene'])):
            #update the light's settings multiple times
            for a in range(config['optimisation']['max_retries']):
                update_bulb(bulb['id'], new_scene)
                time.sleep(config['optimisation']['update_interval'])
            
            bulb['previous_state'] = current_state
            bulb['previous_scene'] = new_scene

            print (current_status['lights'][str(bulb['id'])]['name'], ' - ', new_scene)

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
        'id': bulbs[i]['id'],
        'group': bulbs[i]['group'],
        'previous_state': None,
        'previous_scene': None
    }

#connect to the bridge
b = Bridge(config['ip_address'])
b.connect()

heartbeat_counter = 0
heartbeat_interval = config['heartbeat_interval']/config['optimisation']['polling_interval']

while True:
    time.sleep(config['optimisation']['polling_interval'])

    try:
        bulbs = check_update(bulbs)
    except Exception as e:
        print(f"Error checking bulb: {str(e)}")

    heartbeat_counter += 1
    if heartbeat_counter >= heartbeat_interval:
        print('heartbeat', datetime.now())
        heartbeat_counter = 0