from flask import Flask, request
from enum import Enum
from encryption import *
import platform
from datetime import datetime
import os

if platform.system() == 'Linux':
    LOG_PATH = '/var/log/picroma-authentication.log'
else:
    LOG_PATH = 'picroma-authentication.log'

SERIALS_PATH = 'serials.txt'

Activation = Enum('Activation', 'Logout Activate Login Validate Deactivate Relogin')
SHEET_PLX = 'sheet.plx'

RELEASE_PATH = os.path.join('update', 'release.xml')
TWEAKS_PATH = os.path.join('update', 'PlasmaTweaks.fip')

app = Flask(__name__)

def Log(message):
    now = str(datetime.now())
    fmtstring = f'[{now}] {message}'
    print(fmtstring)
    with open(LOG_PATH, 'a') as f:
        f.write(fmtstring)
        f.write('\n')

def GetAllowedSerials():
    try:
        with open(SERIALS_PATH, 'r') as f:
            lines = set(x for x in f.read().split('\n') if x)
    except FileNotFoundError:
        return None
    return lines
    

def AttemptActivation(encryptedSessionID, activationType):
    sessionID = decrypt(unhexdump(encryptedSessionID), PLASMA_CLIENT_KEY)
    serial, machineID = sessionID[:-160].decode(), sessionID[-160:]
    machineID = decrypt(machineID, PLASMA_SERVER_KEY)
    ip = request.remote_addr
    Log(f'{ip}: Activation: {activationType.name}')
    Log(f'{ip}: Serial: {serial}')
    Log(f'{ip}: Decrypted machine ID: {machineID}')

    allowedSerials = GetAllowedSerials()

    if allowedSerials is None or serial in allowedSerials:
        with open(SHEET_PLX, 'rb') as f:
            plx = f.read()
        encrypted_plx = encrypt(plx, machineID)
        return encrypted_plx
    else:
        return '5'


#Activation

@app.route('/LS/Activation/Logout/')
def Logout():
    return AttemptActivation(request.args.get('id'), Activation.Logout)

@app.route('/LS/Activation/Activate/')
def Activate():
    return AttemptActivation(request.args.get('id'), Activation.Activate)

@app.route('/LS/Activation/Login/')
def Login():
    return AttemptActivation(request.args.get('id'), Activation.Login)

@app.route('/LS/Activation/Validate/')
def Validate():
    return AttemptActivation(request.args.get('id'), Activation.Validate)

@app.route('/LS/Activation/Relogin/')
def Relogin():
    return '0'

@app.route('/LS/Activation/Deactivate/')
def Deactivate():
    return '0'


#Update

#This should be handled by a proper web server
#But this is small enough to keep it self contained for now

@app.route('/Download/Plasma/release.xml')
def Release():
    try:
        with open(RELEASE_PATH, 'r') as f:
            data = f.read()
        return data
    except:
        return None

@app.route('/Download/Plasma/tweaks/PlasmaTweaks.fip')
def Tweaks():
    try:
        with open(TWEAKS_PATH, 'rb') as f:
            data = f.read()
        return data
    except:
        return None


if __name__ == '__main__':
    app.run(port=80)
