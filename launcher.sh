#!/bin/bash

# Activate the virtual environment
source /home/hussain/Desktop/hue/venv/bin/activate

# Change to the hue directory
cd /home/hussain/Desktop/hue

# Run the Python script and log output
python3 bulb.py >> /home/hussain/Desktop/hue/logs/bulb.log 2>&1 &