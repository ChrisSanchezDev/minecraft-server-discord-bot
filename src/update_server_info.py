# -----UPDATING SERVER INFO-----
# Every 30 secs + whenever a user clicks refresh, the program will go thru multiple checks to see the status of the MSILaptop, script, and server itself.
import os
from mcstatus import JavaServer
from datetime import datetime, timedelta

CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
INACTIVE_TIMER = os.getenv('INACTIVE_TIMER')
MSI_IP = os.getenv('MSI_IP')
RCON_PORT = int(os.getenv('RCON_PORT'))
RCON_PASS = os.getenv('RCON_PASSWORD')

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

    # 1. If laptop is on (setup)
    try:
        output = await run_blocking(ping_msi)
        msi_status = int(output.returncode == 0) # 0 == success
    except Exception as e:
        print(f'Ping failed: {e}')
        msi_status = 0

    # 1. If laptop is on (check)
    if msi_status == 1:
        # 2. If server responds (setup)
        try:
            server = await JavaServer.async_lookup(f'{MSI_IP}')
            status = await server.async_status()

            server_status = 1
            player_count = status.players.online
            player_list = [p.name for p in status.players.sample] if status.players.sample else []
            display_status = 'online'

            # 2.1. If server is inactive

            if player_count > 0 and server_status == 1:
                last_active_time = datetime.now()
            else:
                inactive_duration = datetime.now() - last_active_time
                
                if inactive_duration > timedelta(minutes=INACTIVE_TIMER):
                    print(f'No players detected for {INACTIVE_TIMER}. Shutting down server & laptop.')
                    try:
                        client = Client(MSI_IP, RCON_PORT, RCON_PASS)
                        await client.connect()
                        await client.send_cmd('/say No players detected for 30min. Shutting down server & laptop.')
                        await asyncio.sleep(3)
                        await client.send_cmd('/stop')
                        await client.close()
                        server_status = 0
                        print('Server shutdown successful.') 

                        await asyncio.sleep(30)

                        success = await run_blocking(shutdown_msi)

                        if success:
                            msi_status = 0
                            print('MSI Laptop shutdown successful.')
                            return
                        
                    except Exception as e:
                        print(f"Failed to send a stop command: {e}")
                        return

        # 4. else [exception caught] (server is off)
        except Exception as e:
            server_status = 0

            script_status = await run_blocking(check_script_status)
        
            '''
            # Booting: msi_status, script_status, server_status = 1, 1, 0 + Last line timestamp less than 60 seconds ago
            # Crashed: msi_status, script_status, server_status = 1, 1, 0 + Last line timestamp 60 seconds ago or more
            # Offline: msi_status, script_status, server_status = 1, 0, 0 
            '''

            # 4. If script is on
            if script_status == 1:
                display_status = 'booting'
                '''
                # TODO: last_line_age logic
                last_line_age = 0 # For testing now
                
                # 5. If last_line_age is old
                if last_line_age >= 60:
                    display_status = 'crashed'
                    # TODO: Attempt to turn crash report into a log
                    # TODO: Attempt to restart the server in this scenario
                # 6. If last_line_age is still young
                else:
                    display_status = 'booting'
                '''
            
            # 8. else (script off)
            else:
                display_status = 'offline'
        
        # 9. else (laptop off)
        else:
            msi_status, server_status, script_status = 0, 0, 0
            display_status = 'offline'
    
    if display_status != 'online':
        player_count = 0
        player_list = []
    
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