[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
<br><a href="https://www.buymeacoffee.com/4nd3rs" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-black.png" width="150px" height="35px" alt="Buy Me A Coffee" style="height: 35px !important;width: 150px !important;" ></a>

## Information
A simple library for the Visonic PowerMaster API written in Python 3. It is only tested with a PowerMaster-10 using a PowerLink 3 IP module. The PowerLink 3 is a requirement for this library to work.

The **host**, **user_code**, **panel_id**, **user_email**, **user_password** are the same you are using when logging in to your system via the Visonic-GO/BW app,
and **app_id** is just a uniqe id generated from this site: https://www.uuidgenerator.net/ so make sure you replace 00000000-0000-0000-0000-000000000000 with an ID that you generate with that site. There is only support for the -1 partition.

Please be sure that the user is the MASTER USER and you alredy added your panel in your registered account


## Installation
Install with pip3
```
$ sudo pip3 install visonicalarm2
```

## Code examples
### Current status
Getting the current alarm status. Available states are 'AWAY', 'HOME', 'ARMING' or 'DISARM'.
```python
#!/usr/bin/env python3
from visonic import alarm
import logging
_LOGGER = logging.getLogger(__name__)

def main():
	hostname  = 'YOURALARMCOMPANY.tycomonitor.com'
	user_code = '0000'
	app_id   = '00000000-0000-0000-0000-000000000000'
	panel_id  = '99999'
	partition = '-1'
	user_email = "your@email.com"
	user_password = "yourpassword"

	api = alarm.System(hostname, app_id, user_code, user_email, user_password, panel_id, partition)

	res = api.connect()
	res = api.update_devices()
	api.print_system_devices()

if __name__ == '__main__':
	main()

```