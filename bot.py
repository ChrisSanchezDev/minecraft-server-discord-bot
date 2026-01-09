# -----IMPORTS & SETUP-----
import asyncio
import os
import discord
im
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

last_active_time = datetime.now()
server_status = 'offline'

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
        title = '🟢 System Online'
        desc =  f'**{player_count}/12** players connected.'
    elif status == 'booting':
        color = discord.Color.orange()
        title = '🟡 System Booting...'
        desc = 'Please wait for services to start.'
    else:
        color = discord.Color.red()
        title = '🔴 System Offline'
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
    global last_active_time
    global server_status

    # Access the specific channel where the dashboard lives
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return
    
    # TODO: Fix this, booting should occur when:
        # If laptop is on
            # If so, check the status of the script
                # If script enabled but server not responding
                    # 'booting'
                # If script disabled
                    # 'offline'
        # if no laptop
            # 'offline'

    # 1) Is the laptop online?
    try:
        output = subprocess.run
    except Exception as e:

    # If laptop is online, check server_status
    try:
        server = await JavaServer.async_lookup(f'{MSI_IP}')
        status = await server.async_status()

        # If succesful (no crash) + channel is found, we are online
        server_status = 'online'
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
        # If something fails, the server is either offline or unreachable
        server_status = 'offline'
        player_count = 0
        player_list = []
        last_active_time = datetime.now()
    
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