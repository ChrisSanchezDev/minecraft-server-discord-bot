# TODO: Implement daily backup (Probably should be done in another file for modularity)
# TODO: include small images of everyone's face icon when they're online
# TODO: Crashed status
# TODO: Crash logs
# TODO: Auto-restart on Crash
# TODO: Stop button (with the right user perms)
# TODO: Adjust datetime size

# -----IMPORTS & SETUP-----
import os
import discord
from datetime import datetime
from discord.ext import tasks, commands
from dotenv import load_dotenv
from wakeonlan import send_magic_packet

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
MSI_MAC = os.getenv('MAC_ADDRESS')

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

        global display_status
        if display_status != 'offline':
            button.disabled = True
        else: 
            send_magic_packet(MSI_MAC)
            await interaction.followup.send(
                'Magic Packet sent! The server is waking up. The dashboard will update shortly.',
                ephemeral=True
            )
            display_status = 'booting'
        
        embed = create_status_embed(display_status=display_status)
        button.disabled = False

        await interaction.message.edit(embed=embed, view=self)
    
    
    @discord.ui.button(label='Refresh Status', style=discord.ButtonStyle.secondary, custom_id='refresh_btn', emoji='🔄')
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await update_server_info()

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