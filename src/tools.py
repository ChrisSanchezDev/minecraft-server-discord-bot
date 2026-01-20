import asyncio
import os
import paramiko
import subprocess
from dotenv import load_dotenv

load_dotenv()

RCON_PORT = int(os.getenv('RCON_PORT'))
RCON_PASS = os.getenv('RCON_PASSWORD')
SSH_USER = os.getenv('SSH_USER')
SSH_KEY_PATH = os.getenv('SSH_KEY_PATH')
MSI_IP = os.getenv('MSI_IP')

async def run_blocking(func, *args):
    loop = asyncio.get_running_loop() #???: What is get_running_loop
    return await loop.run_in_executor(None, func, *args) # ???: What is .run_in_executor

def ping_msi():
    param = '-n' if os.name == 'nt' else '-c' # -n for Windows, -c for Linux. 
    # .name = nt means Windows
    
    return subprocess.run(
        'ping', param, '1', '-W', '1', MSI_IP, # ???: What is -W
        stdout=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL
    )

def check_script_status():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        private_key = paramiko.RSAKey.from_private_key_file(SSH_KEY_PATH)
        ssh.connect(MSI_IP, username=SSH_USER, pkey=private_key, timeout=5)
        stdin, stdout, stderr = ssh.exec_command('pgrep -f "server.jar"')

        stdout.channel.settimeout(5.0) # If no answer for 5 secs, fail
        script_status = stdout.channel.recv_exit_status() # 0: found, 1: not found

        ssh.close()

        if script_status == 0:
            return 1
        else:
            return 0

    except Exception as e:
        print(f'Script status check failure: {e}')
        return 0

def shutdown_msi():
    print('Attempting MSI Laptop shutdown...')
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        private_key = paramiko.RSAKey.from_private_key_file(SSH_KEY_PATH)
        ssh.connect(MSI_IP, username=SSH_USER, pkey=private_key, timeout=5)
        ssh.exec_command('shutdown -h now')
        ssh.close()
        return True
    except Exception as e:
        print(f'MSI Shutdown Failure: {e}')
        return False