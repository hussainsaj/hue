#documentations
#https://github.com/studioimaginaire/phue

from phue import Bridge
from datetime import datetime
import time
import json
import math
import os
import socket

# Function to check network connectivity
def wait_for_network():
    while True:
        try:
            # Attempt to create a socket connection to Google's DNS server
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            print("Network connected.")
            break
        except OSError:
            print("Network not available, waiting...")
            time.sleep(5)

def load_config(file_name):
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the full path to the config.json file
    config_path = os.path.join(script_dir, file_name)

    #load config
    with open(config_path) as file:
        return json.load(file)

def load_bulbs(bulbs):
    for i in range(len(bulbs)):
        bulbs[i] = {
            'id': bulbs[i]['id'],
            'group': bulbs[i]['group'],
            'previous_state': None,
            'previous_scene': None,
            'update_count': 0
        }
    
    return bulbs

def connect_to_bridge(ip_address):
    b = Bridge(ip_address)
    b.connect()

    return b

#based on time, it returns an appropriate brightness and colour temperature
def get_scene(bulb_group, config):
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
def check_update(bulbs, config):
    current_status = b.get_api()

    #update each bulb in the list
    for i in range(len(bulbs)):
        bulb = bulbs[i]
        current_state = current_status['lights'][str(bulb['id'])]['state']['reachable']
        new_scene = get_scene(bulbs[i]['group'], config)
        update_count = config['optimisation']['update_count']

        #only update if the time based scene has changed or the bulb has turned on or the bulb hasn't been updated enough times
        if (current_state == True and (current_state != bulb['previous_state'] or new_scene != bulb['previous_scene']) and bulb['update_count'] < update_count):

            #update the light's settings multiple times
            #for a in range(config['optimisation']['update_count']):
            #    update_bulb(bulb['id'], new_scene)
            #    time.sleep(config['optimisation']['update_interval'])
            
            update_bulb(bulb['id'], new_scene)
            bulb['update_count'] += 1

            if bulb['update_count'] >= update_count:
                bulb['previous_state'] = current_state
                bulb['previous_scene'] = new_scene
                bulb['update_count'] = 0

                print (current_status['lights'][str(bulb['id'])]['name'], ' - ', new_scene)

        #if the bulb has turned off
        elif (current_state == False and current_state != bulb['previous_state']):
            bulb['previous_state'] = current_state
            bulb['previous_scene'] = new_scene

        bulbs[i] = bulb
    
    return bulbs

if __name__ == "__main__":
    wait_for_network()    
    config = load_config('config.json')
    bulbs = load_bulbs(config['bulbs'])
    b = connect_to_bridge(config['ip_address'])
    
    heartbeat_counter = 0
    heartbeat_interval = config['heartbeat_interval']/config['optimisation']['polling_interval']
    polling_interval = config['optimisation']['polling_interval']

    while True:
        time.sleep(polling_interval)
        try:
            bulbs = check_update(bulbs, config)
        except Exception as e:
            print(f"Error checking bulb: {str(e)}")

        heartbeat_counter += 1
        if heartbeat_counter >= heartbeat_interval:
            print('heartbeat', datetime.now())
            heartbeat_counter = 0