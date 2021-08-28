<h1>Bantool 2</h1>

<h3>New:</h3>
<ul>
<li>Doesn't need a focused window anymore</li>
<li>Controls its own version of Firefox with multiple instances running in parallel</li>
<li>Keeps track of banned users per channel</li>
<li>You can now set multiple channels to run on</li>
</ul>

<h3>How to use:</h3>
<ol>
<li>Unzip FirefoxPortable.7z</li>
<li>navigate to and open \Bantool-Firefox\FirefoxPortable\App\Firefox64\Firefox.exe</li>
<li>type about:profiles into the URL tab</li>
<li>create a new profile called "bantool" save it in the bantool folder \Bantool-Firefox\ <br>
	If it doesn't create a proper profile folder (looks like ugcmlygs.bantool) create one yourself</li>
<li>open bantool profile new window and if needed, set as default
<li>close and reopen firefox
<li>log into Twitch
<li>close out of firefox again
<li>click main.exe or main.py (python 3.8 or newer needs to be installed for the .py file)
<li>It will generate the necessary files and will ask you to press enter to close it
<li><h4>edit the config file:</h4>
<ul>
<li>"twitch_channels": ["NAME OF CHANNEL", "NAME OF SECOND CHANNEL", "NAME OF THIRD CHANNEL"],</li>
<li>"command": true/false,</li>
<li>"Number_of_browser_windows": 1,</li>
<li>"Firefox_profile": "NAME OF PROFILE FOLDER"</li>
<li>"Greeting Emote": the emote it should put in chat once the browser is ready to work</li>
<li>"Chunk size": The number of names after wich a browser window should restart and save its progress (to fix memory leaks)</li>
</ul></li>

<li>The amount of browser windows you should put set is dependent on your computer,<br>
i suggest starting with 1 and working your way up (I can run 8 on a Ryzen 7 3700x)</li>
<li>After filling the namelist and setting the config you can now open the main.exe or main.py again</li>
</ol>


<h3>CVS_Exporter:</h3>
A tool to crudely filter out followbots from your current followers using commanderroots followlist tool (https://twitch-tools.rootonline.de/followerlist_viewer.php) <br>
It will go through the list and if more than 10 people followed in a single second (highly unlikely for normal follows, but common for followbots), it will sort them into the output file

<h3>User_validator</h3>
A tool to filter out users from a namelist if they don't have a valid twitch account anymore

<div>
<h3> If you wanna throw me a few bucks, here is my paypal. (All donations are appreciated but will never be necessary):</h3>
https://www.paypal.com/donate?hosted_button_id=Y6MFY2BENXA2C
</div>

# Installation


## MacOS/Linux

Ensure Python3.8 or 3.9 is installed:

```shell
python3.8 --version
```

Clone this repository and create a virtualenv

```shell
git clone https://github.com/pixelsuchter/Bantool-2.git
cd Bantool-2/
python3.8 -m virtualenv venv
source venv/bin/activate
```

Install the package and verify it was added to the virtualenv path:

```shell
pip install .
bantool --version
```

## Windows

Install Python3.8 or 3.9 from the Microsoft Store.

Open a command prompt window.

- Press Start, type `cmd` and hit Enter
or
- Hit Windows+R, type `cmd` and hit Enter

Clone this repository and create a virtualenv

```shell
git clone https://github.com/pixelsuchter/Bantool-2.git
cd Bantool-2/
python3.8 -m pip install virtualenv
python3.8 -m virtualenv venv
.\\venv\\Scripts\\activate
```

Install the package
```shell
pip install .
```

A `bantool.exe` script will have been created under `.\venv\Scripts`, double-click to generate an empty config file, or copy an existing config file.
