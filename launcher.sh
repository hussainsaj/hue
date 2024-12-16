#!/bin/bash
cd /home/hussain/Desktop/hue
python3 bulb.py >> /home/hussain/Desktop/hue/logs/bulb.log 2>&1 &
cd /