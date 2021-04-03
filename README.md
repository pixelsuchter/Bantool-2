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
<li>"command": "/ban",</li>
<li>"Number_of_browser_windows": 1,</li>
<li>"Firefox_profile": "NAME OF PROFILE FOLDER"</li>
</ul></li>

<li>The amount of browser windows you should put set is dependent on your computer,<br>
i suggest starting with 1 and working your way up (I can run 8 on a Ryzen 7 3700x)</li>
<li>After filling the namelist and setting the config you can now open the main.exe or main.py again</li>
</ol>
