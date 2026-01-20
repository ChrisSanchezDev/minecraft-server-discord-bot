# Necessary dotenv env variables
### discord_bot.py

BOT_TOKEN: Discord bot token
MSI_MAC: MAC address of the server device (MSI Laptop for me)

### logger.py

LOG_FILE: Name of the log file (.log)
LOGGER_NAME: Name for the logger object

### tools.py

RCON_PORT: Port for RCON (Remote Console)
RCON_PASS = Password for RCON
SSH_USER = SSH username for server device
SSH_KEY_PATH = Path for the SSH key (since shutdown can't occur if a password is asked for). I recommend removing all permissions EXCEPT the shutdown command.
MSI_IP = IP address for server device

### ui_templates.py

SERVER_IP: IP address of the minecraft server

### update_server_info.py

CHANNEL_ID: Id of the channel containing the message
INACTIVE_TIMER: Amount of minutes before the server is automatically disabled
MSI_IP = IP address for server device
RCON_PORT: Port for RCON (Remote Console)
RCON_PASS = Password for RCON

### Copy+Paste for .env

BOT_TOKEN=
CHANNEL_ID:
MSI_MAC:
SERVER_IP:
INACTIVE_TIMER