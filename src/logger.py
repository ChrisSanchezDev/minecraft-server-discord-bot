import logging
import os
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# ----- Adjust this section per project -----
LOG_FILE = 'mc-server-discord-bot.log'
LOGGER_NAME = 'Minecwaft-Turtle'
# -------------------------------------------

LOG_STATE = os.getenv('DEBUG_OR_INFO_LOGS')
LOG_ONLY = bool(os.getenv('LOG_ONLY') == 'true')

MAX_BYTES = 5 * 1024 * 1024 # 5MB
BACKUP_COUNT = 3

rotate_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=MAX_BYTES,
    backupCount=BACKUP_COUNT
)

# Standard format
formatter = logging.Formatter('%(asctime) - %(levelname)s - %(name)s - %(message)s')
rotate_handler.setFormatter(formatter)

# Setting up logger object for importing
logger = logging.getLogger(LOGGER_NAME)
if LOG_STATE == 'debug':
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)
logger.addHandler(rotate_handler)

if not LOG_ONLY:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)