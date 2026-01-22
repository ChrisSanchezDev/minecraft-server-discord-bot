from logger import logger
from tools import run_blocking, check_script_status, ping_msi, shutdown_msi
from ui_templates import create_status_embed
from update_server_info import update_server_info
from discord_bot import bot

logger.info('Beginning mc-server-discord-bot...')