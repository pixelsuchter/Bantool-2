Bantool 2

New:

  - Doesn't need a focused window anymore
  - Controls its own version of Firefox with multiple instances running in parallel
  - Keeps track of banned users per channel
  - You can now set multiple channels to run on

DO NOT USE THE CLIPBOARD WHILE THIS TOOL RUNS (no copy/paste)

Namelist at: https://github.com/LinoYeen/Namelists


How to use:
  1)  Unzip FirefoxPortable.7z
  2)  navigate to and open \Bantool-Firefox\FirefoxPortable\App\Firefox64\Firefox.exe
  3)  type about:profiles into the URL tab
  4)  create a new profile called "bantool" save it in the bantool folder \Bantool-Firefox\
      If it doesn't create a proper profile folder (looks like ugcmlygs.bantool) create one yourself
  5)  open bantool profile new window and if needed, set as default
  6)  close and reopen firefox
  7)  log into Twitch
  8)  close out of firefox again
  9)  click main.exe or main.py (python 3.8 or newer needs to be installed for the .py file)
  10) It will generate the necessary files and will ask you to press enter to close it
  11) edit the config.json file:
	- "twitch_channels": ["NAME OF CHANNEL", "NAME OF SECOND CHANNEL", "NAME OF THIRD CHANNEL" ... ],
	- "command": true/false,
	- "Number_of_browser_windows": 1,
	- "Firefox_profile": "NAME OF PROFILE FOLDER"
	- "Greeting Emote": the emote it should put in chat once the browser is ready to work

  12) The amount of browser windows you should put set is dependent on your computer, but 1 per CPU core is reccomended
  14) After filling the namelist and setting the config you can now open the main.exe or main.py again


CVS_Exporter: A tool to crudely filter out followbots from your current followers using commanderroots followlist tool (https://twitch-tools.rootonline.de/followerlist_viewer.php)
It will go through the list and if more than 10 people followed in a single second (highly unlikely for normal follows, but common for followbots), it will sort them into the output file

User_validator: A tool to filter out users from a namelist if they don't have a valid twitch account anymore


If you wanna throw me a few bucks, here is my paypal. (All donations are appreciated but will never be necessary):
https://www.paypal.com/donate?hosted_button_id=Y6MFY2BENXA2C