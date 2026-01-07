# -----IMPORTS & SETUP-----
import os
import discord
from datetime import datetime, timedelta
from discord.ext import tasks, commands
from dotenv import load_dotenv
from wakeonlan import send_magic_packet
from mcrcon import MCRcon
from mcstatus import JavaServer

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
MAC = os.getenv('MAC_ADDRESS')
IP = os.getenv('SERVER_IP')
PORT = int(os.getenv('PORT'))
RCON_PASS = os.getenv('RCON_PASSWORD')

last_active_time = datetime.now()
current_state = 'offline'

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# -----DASHBOARD SETUP-----
def create_status_embed(status='offline', player_count=0, player_list=None):
    if player_list is None:
        player_list = []
    
    if status == 'online':
        color = discord.Color.green()
        title = '🟢 System Online'
        desc =  f'**{player_count}/12** players connected.'
    elif status == 'booting':
        color = discord.Color.orange()
        title = '🟡 System Booting...'
        desc = 'Please wait ~2 minutes for services to start.'
    else:
        color = discord.Color.red()
        title = '🔴 System Offline'
        desc = 'Click the button below to start the server'

    embed = discord.Embed(title=title, description=desc, color=color)
    embed.add_field(name='Server Address', value=f'{IP}', inline=False)

    # Showing player names if server is Online
    if status == 'online' and player_list:
        embed.add_field(name='Online Users', value='\n'.join(player_list), inline=False)

    embed.set_footer(text='Minecwaft-Turtle • Refreshes every 30s')
    
    return embed

async def get_server_info():
    global last_active_time
    global current_state

    # Access the specific channel where the dashboard lives
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return
    
    try:
        server = await JavaServer.async_lookup(f'{IP}')
        status = await server.async_status()

        # If succesful (no crash) + channel is found, we are online
        current_state = 'online'
        player_count = status.players.online
        player_list = [p.name for p in status.players.sample] if status.players.sample else []

        # -----WITHIN: AUTO-SHUTDOWN LOGIC-----
        if player_count > 0:
            last_active_time = datetime.now()
        else:
            inactive_duration = datetime.now() - last_active_time
            
            if inactive_duration > timedelta(minutes=30):
                try:
                    with MCRcon(IP, RCON_PASS, PORT) as mcr:
                        mcr.command("/say No players detected for 30min! Shutting down...")
                        mcr.command("/stop")

                    current_state = 'offline'
                    print('No players detected for 30min. Shutting down server & laptop.')
                except Exception as e:
                    print(f"Failed to send RCON stop command: {e}")
    
    except Exception as e:
        # If something fails, the server is either offline or unreachable
        current_state = 'offline'
        player_count = 0
        player_list = []
        last_active_time = datetime.now()
    
    # Generate a UI card using our factory function
    embed = create_status_embed(status=current_state, player_count=player_count, player_list=player_list)
    view = ServerControlView()

    # Find the existing Dashboard msg or create a new one
    last_message = None
    async for message in channel.history(limit=1):
        if message.author == bot.user:
            last_message = message
            break

    if last_message:
        # Edit the existing message
        await last_message.edit(embed=embed, view=view)
    else:
        # No dashboard found, so make a new one
        await channel.send(embed=embed, view=view)

class ServerControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Button never expires

    @discord.ui.button(label='Start Server', style=discord.ButtonStyle.green, custom_id='start_btn', emoji='⚡')
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        if current_state == 'online':
            await interaction.followup.send(
                'Vro, server is already online!',
                ephemeral=True
            )
            return

        send_magic_packet(MAC)

        await interaction.followup.send(
            'Magic Packet sent! The server is waking up. The dashboard will update shortly.',
            ephemeral=True
        )

        embed = create_status_embed(status='booting')

        button.disabled = True
        await interaction.message.edit(embed=embed, view=self)
    
    @discord.ui.button(label='Refresh Status', style=discord.ButtonStyle.secondary, custom_id='refresh_btn', emoji='🔄')
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await get_server_info()

# -----BACKGROUND LOOPS & EVENTS-----
@tasks.loop(seconds=30)
async def update_status():
    await get_server_info()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')

    # Background loop
    if not update_status.is_running():
        update_status.start()

    # Re-registering the Button view
    # Required for persistent views to work after a bot restarts
    bot.add_view(ServerControlView())

    print ('Dashboard is now active and listening for inputs.')

if __name__ == '__main__':
    bot.run(BOT_TOKEN)