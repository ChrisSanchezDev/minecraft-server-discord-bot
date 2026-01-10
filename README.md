# HomeLab: minecraft-server-discord-bot

Automated Discord Bot that turns on an old MSI laptop thru Wake-On-LAN upon user request, which in turn also turns starts up a modded Minecraft server. When there are no players for 30 minutes, the server and laptop will automatically shutdown to conserve power.

The bot itself shares the status of the server on discord thru a Discord Bot, which is hosted 24/7 on my Raspberry Pi 4. Additionally, users can start the server whenever it's down and can see the amount of players on the server + their usernames.

This repo specifically just entails the code for the discord bot's functions. It doesn't include the current setup of the MSI Laptop or the attachment of this script to my Raspberry Pi 4 whenever it boots or reboots.

## Known Issues:

* Booting seems inconsistent. While booting up, the status will tend to jump from booting, to offline, to online.
    * Booting should specifically be enabled when the laptop is on and the server is in the progress of starting up (the script is active but the server isn't)
* Laptop isn't properly being shutdown (maybe a shutdown permissions issue?)
