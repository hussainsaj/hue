# hue
automatic controller for hue bulbs

## Getting started

In terminal, navigate to the directory

Create a virtual environment

`
python3 -m venv .venv
`

Activate the virtual environment

`
source .venv/bin/activate
`

Install dependencies

`
pip install -r requirements.txt
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