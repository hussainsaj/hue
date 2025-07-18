#documentations
#https://github.com/studioimaginaire/phue

from phue import Bridge
from datetime import datetime, timedelta
import time
import json
import math
import os
import socket
import logging

# Function to check network connectivity
def wait_for_network():
    while True:
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            logging.info("Network connected.")
            break
        except OSError:
            logging.error("Network not available. Waiting...")
            time.sleep(5)

def load_config(file_name):
    #load config
    with open(file_name) as file:
        return json.load(file), os.path.getmtime(file_name)

# check if the config file has been modified since last checked
def update_config(config, config_last_modified, file_name):
    if (os.path.getmtime(file_name) > config_last_modified):
        logging.info("Configuration file has been modified. Reloading configuration.")
        return load_config(file_name)
    else:
        return config, config_last_modified

def load_bulbs(groups):
    for group in groups:
        for i in range(len(groups[group]['bulbs'])):
            groups[group]['bulbs'][i] = {
                'id': groups[group]['bulbs'][i],
                'previous_state': None,
                'previous_scene': None,
                'update_count': 0
            }
    
    return groups

def connect_to_bridge(ip_address):
    try:
        b = Bridge(ip_address)
        b.connect()
    except Exception as e:
        logging.exception("Failed to connect to the bridge. Retrying in 1 minute.")
        time.sleep(60)
        connect_to_bridge(ip_address)
    
    return b

#updates the bulb state
def update_bulb(bulb, scene, current_status):
    reachable = current_status['lights'][str(bulb['id'])]['state']['reachable']
    update_count = config['optimisation']['update_count']
    on = current_status['lights'][str(bulb['id'])]['state']['on']

    scene['on'] = True

    #only update if the time based scene has changed or the bulb has turned on or the bulb hasn't been updated enough times
    if (reachable == True and (reachable != bulb['previous_state'] or scene != bulb['previous_scene'] or on == False) and bulb['update_count'] < update_count):
        b.set_light(bulb['id'], scene)

        bulb['update_count'] += 1

        if bulb['update_count'] >= update_count:
            bulb['previous_state'] = reachable
            bulb['previous_scene'] = scene
            bulb['update_count'] = 0

            logging.info(f"Updated: {current_status['lights'][str(bulb['id'])]['name']} - {scene}")

    #if the bulb has turned off
    elif (reachable == False and reachable != bulb['previous_state']):
        bulb['previous_state'] = reachable
        bulb['previous_scene'] = scene

    return bulb

#checks for any changes for each bulb
def check_update(groups, current_status):
    #based on time, it returns an appropriate brightness and colour temperature
    def get_scene(bulb_group, config):
        #function to calculate the time difference
        def calculate_time_difference(time1, time2):
            time_format = "%H:%M"

            time1 = datetime.strptime(time1, time_format)
            time2 = datetime.strptime(time2, time_format)

            difference = time2 - time1
            difference_in_minutes = int(difference.total_seconds() / 60)

            return abs(difference_in_minutes)

        #creates a new scene
        def calculate_scene(difference, current_scene, next_scene, transistion_period):
            new_scene = {}
            interpolation_factor = difference / transistion_period

            for key in current_scene:
                if key == 'on':
                    new_scene[key] = True
                    continue
                
                current_value = current_scene[key]
                next_value = next_scene[key]
                new_value = next_value + ((current_value - next_value) * interpolation_factor)
                
                new_scene[key] = math.floor(new_value)

            return new_scene

        scenes = config['scenes']

        time_slots = config['groups'][bulb_group]['time_slots']
        transistion_period = config['groups'][bulb_group]['transistion_period']

        now = datetime.now().strftime("%H:%M")

        sorted_times = sorted(time_slots.keys())

        #default value, last scene in the list
        new_scene = scenes[time_slots[sorted_times[-1]]]

        #finds the current scene
        for i in range(len(sorted_times)):
            if now < sorted_times[i]:
                difference = calculate_time_difference(now, sorted_times[i])

                #Calculate transition if within transition period
                if difference <= transistion_period:
                    new_scene = calculate_scene(difference, scenes[time_slots[sorted_times[i-1]]], scenes[time_slots[sorted_times[i]]], transistion_period)
                else:
                    new_scene = scenes[time_slots[sorted_times[i-1]]]

                break

        return new_scene

    for group in groups:
        new_scene = get_scene(group, config)

        for i in range(len(groups[group]['bulbs'])):
            groups[group]['bulbs'][i] = update_bulb(groups[group]['bulbs'][i], new_scene, current_status)
    
    return groups

def check_automation(automations, current_status):
    # Updated interpolate function with a customizable time window
    def interpolate_values(target_time, window_minutes, data):
        today_str = datetime.now().strftime("%Y-%m-%d")
        target_dt = datetime.strptime(f"{today_str} {target_time}", "%Y-%m-%d %H:%M")
        start_dt = target_dt - timedelta(minutes=window_minutes)
        current_dt = datetime.now()

        # Check if current time is within the range
        if current_dt < start_dt or current_dt > target_dt - timedelta(minutes=1):
            return None  # Time is outside the range

        # Calculate the elapsed time fraction (0 means start, 1 means target time)
        total_seconds = (target_dt - start_dt).total_seconds()
        elapsed_seconds = (current_dt - start_dt).total_seconds()
        fraction = elapsed_seconds / total_seconds
    
        # Interpolate each of brightness, hue, and saturation
        brightness = data['bri'][round(len(data['bri']) * fraction)]
        hue = data['hue'][round(len(data['hue']) * fraction)]
        saturation = data['sat'][round(len(data['sat']) * fraction)]

        return {
            'bri': brightness,
            'hue': hue,
            'sat': saturation
        }

    for automation in automations:
        duration = automations[automation]['duration']
        time = automations[automation]['time']
        data = automations[automation]['data']
        active_days = automations[automation]['active_days']

        # Check if the automation should run today
        if datetime.now().weekday() not in active_days:
            continue

        scene = interpolate_values(time, duration, data)
        
        if scene is not None:
            for i in range (len(automations[automation]['bulbs'])):
                update_bulb(automations[automation]['bulbs'][i], scene, current_status)
    
    return

if __name__ == "__main__":
    # Ensure the 'logs' directory exists
    os.makedirs("logs", exist_ok=True)

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        filename=f"logs/{datetime.now().strftime('%Y-%m-%d')}.log",
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        filemode='w'
    )

    logging.info("Starting bulb automation script.")

    # Wait for network connectivity before proceeding
    wait_for_network()

    # Load configuration and initialize bulbs and bridge connection
    config, config_last_modified = load_config('config.json')
    groups = load_bulbs(config['groups'])
    automations = load_bulbs(config['automations'])
    b = connect_to_bridge(config['ip_address'])
    
    polling_interval = config['optimisation']['polling_interval']
    heartbeat_interval = config['optimisation']['heartbeat_interval']/polling_interval
    heartbeat_counter = 0

    current_status = None

    # Main loop to check for updates and apply changes
    while True:
        config, config_last_modified = update_config(config, config_last_modified, 'config.json')

        try:
            current_status = b.get_api()
        except Exception as e:
            logging.exception("Bridge not connected.")
            time.sleep(5)
            continue
        
        try:
            groups = check_update(groups, current_status)
        except Exception as e:
            logging.exception("Error updating bulbs.")
        
        try:
            check_automation(automations, current_status)
        except Exception as e:
            logging.exception("Error updating automations.")

        heartbeat_counter += 1
        if heartbeat_counter >= heartbeat_interval:
            logging.info("Heartbeat")
            heartbeat_counter = 0
        
        time.sleep(polling_interval)
        
        #logging
        #time.sleep(30)
        #import csv
        #def save_light_data(time, brightness, hue, saturation, file_name='light_data.csv'):
        #    file_exists = os.path.isfile(file_name)
        #    with open(file_name, mode='a', newline='') as file:
        #        writer = csv.writer(file)
        #        if not file_exists:
        #            writer.writerow(['Time', 'Brightness', 'Hue', 'Saturation'])
        #        writer.writerow([time, brightness, hue, saturation])
        #current_status = b.get_api()['lights']['4']['state']
        #print(datetime.now().strftime('%Y-%m-%d %H:%M'), current_status)
        #save_light_data(datetime.now().strftime('%Y-%m-%d %H:%M'), current_status['bri'], current_status['hue'], current_status['sat'])

        #manual update
        #b.set_light(4, {"bri": 254, "hue": 41440, "sat": 75})