# hue
automatic controller for hue bulbs

## Getting started

In terminal, navigate to the directory

Create a virtual environment

`
python3 -m venv env
`

Activate the virtual environment

`
source env/bin/activate
`

Install dependencies

`
pip install phue
`

Exit the virtual environment

`
deactivate
`

## Running the script in terminal

Activate the virtual environment and run script in terminal

`
python3 bulb.py
`

## Add job in crontab

Open crontab

`
sudo crontab -e
`

Add the job

`
@reboot /home/hussain/Desktop/hue/launcher.sh
`

Save and give permission to launcher.sh

`
chmod +x launcher.sh
`

Reboot

`
sudo reboot
`