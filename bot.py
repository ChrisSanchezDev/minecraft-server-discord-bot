# TODO: Implement daily backup (Probably should be done in another file for modularity)

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
MSI_IP = os.getenv('MSI_IP')
SERVER_IP = os.getenv('SERVER_IP')
RCON_PORT = int(os.getenv('RCON_PORT'))
RCON_PASS = os.getenv('RCON_PASSWORD')

# 0 means off, 1 means on
msi_status, script_status, server_status = 0, 0, 0 # ??? Does this only happen at the start or do we constantly do this.
display_status = 'offline'
last_active_time = datetime.now()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# -----DASHBOARD SETUP-----
# Factory function, sole goal of creating the embed display based on what's given
def create_status_embed(display_status='offline', player_count=0, player_list=None):
    if player_list is None:
        player_list = []
    
    # Dependent on received status
    if display_status == 'offline':
        color = discord.Color.red()
        title = '🔴 Server Offline'
        desc = 'Click the button below to start the server.'
    elif display_status == 'crashed':
        color = discord.Color.yellow()
        title = 'WARNING EMOJI Server Crashed' # TODO: Warning emoji
        desc = 'oop, a server restart is required.'
    elif display_status == 'booting':
        color = discord.Color.orange()
        title = '🟡 Server Booting...' # TODO: Replace w/ orange emoji
        desc = 'Please wait for services to start.'
    else:
        color = discord.Color.green()
        title = '🟢 Server Online'
        desc =  f'**{player_count}/12** players connected.'

    embed = discord.Embed(title=title, description=desc, color=color)
    embed.add_field(name='IP Address', value=f'{SERVER_IP}', inline=False)

    # Showing player names when online
    if display_status == 'online' and player_list:
        # TODO: include small images of everyone's face icon
        embed.add_field(name='Online Users', value='\n'.join(player_list), inline=False)

    embed.set_footer(text='Minecwaft-Turtle • Refreshes every 30s')
    
    return embed

# -----UPDATING SERVER INFO-----
# Every 30 secs + whenever a user clicks refresh, the program will go thru multiple checks to see the status of the MSILaptop, script, and server itself.
async def update_server_info():
    global display_status
    global msi_status
    global server_status
    global script_status
    global last_active_time

    # Access the specific channel where the dashboard lives
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return
    
    '''
    # Logic Path for Checking Statuses
    # 1. If laptop is on - +
        # 2.if server responds +
            # 'online'
            # 2.1. If server is inactive
                # 'offline'
        # 3. else [exception caught] (server not responding) - 
            # 4. if script is on
                # 5. if display status is already 'crashed', assume it's still crashed
                # 6. if last_line_age is old
                    # 'crashed'
                    # 6.1. create crash.log
                    # 6.2. shutdown server (auto restart?)
                # 7. else: (last_line_age still young)
                    # 'booting'
            # 8. else (script off) -
                # 'offline'
    # 9. else (laptop off)
        # 'offline'
    # Most of the time, the server will be offline and this allows for the fastest check on that + accounting for all variations of the status.
    '''

    # 1. If laptop is on (setup)
    try:
        # Will return a 0 on success, non-zero on failure
        output = subprocess.run(
            # '-c 1' is for Linux, '-n 1' would be for Windows
            ['ping','-c 1', '1', MSI_IP],
            stdout=subprocess.DEVNULL, # Hides the output since it's long and kinda useless rn
            stderr=subprocess.DEVNULL
        )
        msi_status = int(output.returncode == 0)
    except Exception as e:
        print(f'Ping failed: {e}')
        msi_status = 0

    # 1. If laptop is on (check)
    if msi_status == 1:
        # 2. If server responds (setup)
        try:
            # Tries to get a response from the server thru localhost
            # If the server is online, the try block will continue
            # If it's offline, server will return an error and the program will jump to the exception block.
            server = await JavaServer.async_lookup(f'{MSI_IP}')
            status = await server.async_status()

            # No crash, so server is on
            server_status = 1
            player_count = status.players.online
            player_list = [p.name for p in status.players.sample] if status.players.sample else []
            display_status == 'online'

            # 2.1. If server is inactive
            # Inactive: 30 mins with no players

            # Players are online
            if player_count > 0 and server_status == 'online':
                last_active_time = datetime.now()
            
            # Check if server is inactive for 30+ mins
            else:
                inactive_duration = datetime.now() - last_active_time
                
                if inactive_duration > timedelta(minutes=30):
                    print('No players detected for 30min. Shutting down server & laptop.')
                    try:
                        client = Client(MSI_IP, RCON_PORT, RCON_PASS)
                        await client.connect()

                        await client.send_cmd('/say No players detected for 30min. Shutting down server & laptop.')
                        await client.send_cmd('/stop')
                        await client.close()

                        server_status = 0
                        print('Server shutdown successful.')

                        # TODO: Laptop shutdown logic
                        # TODO: Give the server atleast 30 secs so that things are saved properly + allow time to cancel the shutdown.
                        asyncio.sleep(30)
                        ssh = paramiko.SSHClient()

                        msi_status = 0
                        print('MSI Laptop shutdown successful.')
                        return

                    except Exception as e:
                        print(f"Failed to send stop command: {e}")
                        return

        # 4. else [exception caught] (server is off)
        except Exception as e:
            # If something fails, the server is either booting, crashed, or offline.
            server_status = 0

            # TODO: Get a response about the status of the script
            # script_status = 
            
            '''
            # Booting: msi_status, script_status, server_status = 1, 1, 0 + Last line timestamp less than 60 seconds ago
            # Crashed: msi_status, script_status, server_status = 1, 1, 0 + Last line timestamp 60 seconds ago or more
            # Offline: msi_status, script_status, server_status = 1, 0, 0 
            '''

            # 4. If script is on
            if script_status == 1:
                # 5. If we crash, we shouldnt assume that it'll go back to booting
                # TODO: Possibly remove this. If we auto shutdown, we might have the situation where we go from crash to booting
                # if display_status == 'crashed':
                    
                # TODO: Properly gauge if a line has moved or not
                last_line_age = 0
                
                # 6. If last_line_age is longer than 60, server most likely crashed
                if last_line_age >= 60:
                    display_status = 'crashed'
                    # TODO: Attempt to turn the crash report into a log
                    # TODO: Possibly attempt to shutdown the server in this scenario
                # 7. If last_line_age is still young, server is most likely booting.
                else:
                    display_status = 'booting'
            
            # 8. else (script off)
            else:
                display_status == 'offline'
        
        # 9. else (laptop off)
        else:
            msi_status, server_status, script_status = 0, 0, 0
            display_status = 'offline'
    
    if not display_status == 'online':
        player_count = 0
        player_list = []
    
    # Generate a UI card using our factory function
    embed = create_status_embed(display_status=display_status, player_count=player_count, player_list=player_list)
    view = ServerControlView()

    # Find the existing Dashboard msg or create a new one
    last_message = None
    async for message in channel.history(limit=1):
        if message.author == bot.user:
            last_message = message
            break

    if last_message:
        old_embed = last_message.embeds[0] if last_message.embeds else None

        if old_embed and (old_embed.description == embed.description) and (old_embed.color == embed.color):
            print("Status unchanged. Skipping Discord edit to prevent rate limits.")
            pass
        else:
            await last_message.edit(embed=embed, view=view)
            print("Status changed! Updating dashboard...")
    else:
        # No old dashboard found, so make a new one
        await channel.send(embed=embed, view=view)

# Controlling the server thru buttons
class ServerControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Button never expires

    @discord.ui.button(label='Start Server', style=discord.ButtonStyle.green, custom_id='start_btn', emoji='⚡')
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Gives a defer message to discord (it asks for Discord to wait longer for a response)
        await interaction.response.defer(ephemeral=True)

        if display_status != 'offline':
            button.disabled = True

        send_magic_packet(MSI_MAC) # ??? If this doesn't work, will it crash or just continue?

        await interaction.followup.send(
            'Magic Packet sent! The server is waking up. The dashboard will update shortly.',
            ephemeral=True
        )

        embed = create_status_embed(display_status='booting')

        button.disabled = True # ??? Does this gray out the button?
        await interaction.message.edit(embed=embed, view=self)
    
    @discord.ui.button(label='Refresh Status', style=discord.ButtonStyle.secondary, custom_id='refresh_btn', emoji='🔄')
    async def refresh_button(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await update_server_info()

# -----BACKGROUND LOOPS & EVENTS-----
@tasks.loop(seconds=30)
async def periodically_update_status():
    await update_server_info()

@bot.event
async def on_ready():
    print(f'Logged in as BOT:{bot.user} (ID: {bot.user.id})')

    # Begin 30 sec loop
    if not periodically_update_status.is_running():
        periodically_update_status.start() # ??? Shouldnt we use asyncio for running this? What differs using asyncio vs. not using asyncio for async python functions.

    # Re-registering the Button view
    # Required for persistent views to work after a bot restarts
    bot.add_view(ServerControlView())

    print ('Dashboard is now active and listening for inputs.')

if __name__ == '__main__':
    bot.run(BOT_TOKEN)