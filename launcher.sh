#!/bin/bash

# Change to the hue directory
cd /home/hussain/Desktop/hue

# Activate the virtual environment
source env/bin/activate

# Run the Python script and log output
python3 bulb.py >> logs/bulb.log 2>&1 &