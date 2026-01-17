# TODO: Implement daily backup (Probably should be done in another file for modularity)
# TODO: include small images of everyone's face icon when they're online
# TODO: Crashed status
# TODO: Crash logs
# TODO: Auto-restart on Crash
# TODO: Stop button (with the right user perms)

# -----IMPORTS & SETUP-----
import asyncio 
import os
import discord
import paramiko
import subprocess
from aiomcrcon import Client
from datetime import datetime, timedelta
from discord.ext import tasks, commands
from dotenv import load_dotenv
from wakeonlan import send_magic_packet
from mcstatus import JavaServer

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
MSI_MAC = os.getenv('MAC_ADDRESS')
SERVER_IP = os.getenv('SERVER_IP')
INACTIVE_TIMER = os.getenv('INACTIVE_TIMER')

# 0 means off, 1 means on
msi_status, script_status, server_status = 0, 0, 0
display_status = 'offline'
last_active_time = datetime.now()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Controlling the server thru buttons
class ServerControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Button never expires

    @discord.ui.button(label='Start Server', style=discord.ButtonStyle.green, custom_id='start_btn', emoji='⚡')
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        if display_status != 'offline':
            button.disabled = True

        send_magic_packet(MSI_MAC)
        await interaction.followup.send(
            'Magic Packet sent! The server is waking up. The dashboard will update shortly.',
            ephemeral=True
        )

        embed = create_status_embed(display_status='booting')
        button.disabled = True #

        await interaction.message.edit(embed=embed, view=self)
    
    @discord.ui.button(label='Refresh Status', style=discord.ButtonStyle.secondary, custom_id='refresh_btn', emoji='🔄')
    async def refresh_button(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await update_server_info()
    
    ''' Stop Server button for when no one is on the server (Maybe we can have it so if you have a specific role, you can turn it off at anytime)
    @discord.ui.button(label='Stop Server', style=discord.ButtonStyle.red, custom_id='stop_btn', emoji='⛔')
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Gives a defer message to discord (it asks for Discord to wait longer for a response)
        await interaction.response.defer(ephemeral=True)

        if display_status != 'online':
            button.disabled = True

        send_magic_packet(MSI_MAC) # ??? If this doesn't work, will it crash or just continue?

        await interaction.followup.send(
            'Magic Packet sent! The server is waking up. The dashboard will update shortly.',
            ephemeral=True
        )

        embed = create_status_embed(display_status='booting')

        button.disabled = True # ??? Does this gray out the button?
        await interaction.message.edit(embed=embed, view=self)
    '''

# -----BACKGROUND LOOPS & EVENTS-----
@tasks.loop(seconds=30)
async def periodically_update_status():
    await update_server_info()

@bot.event
async def on_ready():
    print(f'Logged in as BOT:{bot.user} (ID: {bot.user.id})')

    if not periodically_update_status.is_running():
        periodically_update_status.start()

    # Required for persistent views to work after a bot restarts
    bot.add_view(ServerControlView())

    print ('Dashboard is now active and listening for inputs.')

if __name__ == '__main__':
    bot.run(BOT_TOKEN)