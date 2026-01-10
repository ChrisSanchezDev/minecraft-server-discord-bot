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
MAC = os.getenv('MAC_ADDRESS')
MSI_IP = os.getenv('MSI_IP')
SERVER_IP = os.getenv('SERVER_IP')
RCON_PORT = int(os.getenv('RCON_PORT'))
RCON_PASS = os.getenv('RCON_PASSWORD')

# 0 means off, 1 means on
msi_status = 0
server_status = 0
script_status = 0
display_status = 'offline'
last_active_time = datetime.now()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# -----DASHBOARD SETUP-----
def create_status_embed(status='offline', player_count=0, player_list=None):
    if player_list is None:
        player_list = []
    
    # Dependent on received status
    if status == 'online':
        color = discord.Color.green()
        title = '🟢 Server Online'
        desc =  f'**{player_count}/12** players connected.'
    elif status == 'booting':
        color = discord.Color.orange()
        title = '🟡 Server Booting...'
        desc = 'Please wait for services to start.'
    else:
        color = discord.Color.red()
        title = '🔴 Server Offline'
        desc = 'Click the button below to start the server'

    embed = discord.Embed(title=title, description=desc, color=color)
    embed.add_field(name='IP Address', value=f'{SERVER_IP}', inline=False)

    # Showing player names when online
    if status == 'online' and player_list:
        embed.add_field(name='Online Users', value='\n'.join(player_list), inline=False)

    embed.set_footer(text='Minecwaft-Turtle • Refreshes every 30s')
    
    return embed

# -----UPDATING SERVER INFO-----
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
    
    # TODO: Fix this, booting should occur when:
        # Option A OFFLINE SERVER- ONLINE SERVER+
        # 1. If laptop is on - +
            # 2.if server responds +
                # 'online'
            # 3. else (server not responding) - 
                # 4. if script is on
                    # 5. if display_status isnt alrdy 'crashed' and script is moving
                        # 'booting'
                    # 6. else (display_status says 'crashed' or script isn't moving)
                        # 'crashed'
                # 7. else (script off) -
                    # 'offline'
        # 8. else (laptop off)
            # 'offline'
        
        # Option B OFFLINE SERVER- ONLINE SERVER+
        # 1. if laptop is on - +
            # 2. if script is on +
                # 3. if server is on +
                    # 'online'
                # 4. else (server off)
                    # 5. if display_status isnt alrdy 'crashed' and script is moving
                        # 'booting'
                    # 6. else (display_status says 'crashed' or script isn't moving)
                        # 'crashed'
            # 7. else (script off) -
                # 'offline'
        # 8. else (laptop off)
            # 'offline'

        ## Option A ends up being more checks when server is offline, but less if it's online
        ## Option B ends up being more checks when server is online, but less if it's offline
        ## I think I prefer Option B since, more often than not, the server is going to be offline for more hours in the day.
        ## But is it more pricey to check if the server is offline or check the script on the MSI laptop? Honestly, if the laptop is on but server off, it shouldnt really matter too much, so maybe Option A is better since most times, the server will be online if the laptop is on.

        ## The display_status == crashed check is mainly because there's a very very small chance that you'll ever go from a crash directly to a boot without having first gone offline. It'll also save us from constant log reading whenever a server crashes.

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
            server = await JavaServer.async_lookup(f'{MSI_IP}')
            status = await server.async_status()

            # If response didnt crash, server is online
            server_status = 1
            player_count = status.players.online
            player_list = [p.name for p in status.players.sample] if status.players.sample else []

            # -----WITHIN: AUTO-SHUTDOWN LOGIC-----
            if player_count > 0 and server_status == 'online':
                last_active_time = datetime.now()
            else:
                inactive_duration = datetime.now() - last_active_time
                
                if inactive_duration > timedelta(minutes=30):
                    print('No players detected for 30min. Shutting down server & laptop.')
                    try:
                        client = Client(MSI_IP, RCON_PORT, RCON_PASS)
                        await client.connect()

                        await client.send_cmd('/say No players detected for 30min. Shutting down server & laptop.')
                        await client.send_cmd('/stop')

                        # ------
                        # Either this or just have it check the laptop, then script status
                        await client.close()

                        server_status = 'offline'
                        print('Shutdown successful.')
                        # ------
                    except Exception as e:
                        print(f"Failed to send RCON stop command: {e}")
    
        except Exception as e:
            # If something fails, the server is either booting, crashed, or offline.
            # Booting: Laptop on, Server off, Script on, Last line timestamp less than 60 seconds ago
            # Crashed: Laptop on, Server off, Script on, last line timestamp 60 seconds ago or more
            # Offline: Laptop on, Server off, Script off.
            # All of them will have 0 players currently.
            player_count = 0
            player_list = []
            last_active_time = datetime.now()

            # Boot/Crash Check
            # If we crash, we shouldnt assume that it'll go back to booting 
            if script_status == 0
            # SSH into the MSI Laptop
            # Check the script
            # TWO OPTIONS:
            # Option A: If last line hasnt changed in 60 seconds
                # 'crashed'
            # else: 'booting'
            # Option B: If last line timestamp is 60 secs+ from now
                # 'crashed'
            # else: 'booting'

            
    
    # Generate a UI card using our factory function
    embed = create_status_embed(status=server_status, player_count=player_count, player_list=player_list)
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
        # No dashboard found, so make a new one
        await channel.send(embed=embed, view=view)

class ServerControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Button never expires

    @discord.ui.button(label='Start Server', style=discord.ButtonStyle.green, custom_id='start_btn', emoji='⚡')
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        if server_status == 'online':
            await interaction.followup.send(
                'Vro, server is already online!',
                ephemeral=True
            )
            return
        elif server_status == 'booting':
            await interaction.followup.send(
                'Vro, server is already booting up! (If more than 2 mins have alrdy passed, it might be stuck...)',
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
        await update_server_info()

# -----BACKGROUND LOOPS & EVENTS-----
@tasks.loop(seconds=30)
async def periodically_update_status():
    await update_server_info()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')

    # Background loop
    if not periodically_update_status.is_running():
        periodically_update_status.start()

    # Re-registering the Button view
    # Required for persistent views to work after a bot restarts
    bot.add_view(ServerControlView())

    print ('Dashboard is now active and listening for inputs.')

if __name__ == '__main__':
    bot.run(BOT_TOKEN)