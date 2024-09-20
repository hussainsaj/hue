#!/bin/bash
cd /home/ussama/Desktop/hue
python3 bulb.py >> /home/ussama/Desktop/hue/logs/bulb.log 2>&1 &
cd /