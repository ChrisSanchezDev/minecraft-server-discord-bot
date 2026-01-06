import os
import discord
from discord.ext import tasks, commands
from dotenv import load_dotenv
from wakeonlan import send_magic_packet
from mcstatus import JavaServer

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
MAC = os.getenv('MAC_ADDRESS')
IP = os.getenv('SERVER_IP')
PORT = int(os.getenv('SERVER_PORT'))

intents = discord.Intents.default()
intents.message = True
intents.message_content = True

bot = commands.Bot(commands_prefix='!', intents=intents)

# Generating a visual card based on the state
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
        desc = 'Please wait ~1 minute for services to start.'
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


class ServerControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Button never expires

    @discord.ui.button(label='Start Server', style=discord.ButtonStyle.green, custom_id='start_btn', emoji='⚡')
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        # LATER: Check if already online

        send_magic_packet(MAC)

        await interaction.followup.send(
            'Magic Packet Sent! ther server is waking up. The dashboard will update shortly.',
            ephermal=True
        )

        embed = create_status_embed(status='booting')

        button.disabled = True
        await interaction.message.edit(embed=embed, view=self)

    @