# send_to_daris
A plugin app for MyTardis (Django) to send data to DaRIS

## Installation

1. Clone **send_to_daris** into your mytardis apps directory:
  * `cd /opt/mytardis/tardis/apps`
  * `git clone https://github.com/uom-daris/send_to_daris.git`
2. Add **send_to_daris** plugin app to the INSTALLED_APPS setting in **tardis/settings.py**:
  * `INSTALLED_APPS += ('tardis.apps.send_to_daris',)`
3. Insert UI elements to MyTardis web portal
