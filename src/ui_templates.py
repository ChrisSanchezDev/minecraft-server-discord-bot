# -----DASHBOARD SETUP-----
# Factory function
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
        title = '⚠️ Server Crashed'
        desc = 'oop, a server restart is required.'
    elif display_status == 'booting':
        color = discord.Color.orange()
        title = '🟠 Server Booting...'
        desc = 'Please wait for services to start. (If longer than 3 mins, it prolly crashed)'
    else:
        color = discord.Color.green()
        title = '🟢 Server Online'
        desc =  f'**{player_count}/12** players connected.'

    embed = discord.Embed(title=title, description=desc, color=color)
    embed.add_field(name='IP Address', value=f'{SERVER_IP}', inline=False)

    if display_status == 'online' and player_list:
        embed.add_field(name='Online Users', value='\n'.join(player_list), inline=False)

    embed.set_footer(text='Minecwaft-Turtle • Refreshes every 30s')
    
    return embed