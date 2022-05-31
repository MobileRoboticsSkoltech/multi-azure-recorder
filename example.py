from fastapi import FastAPI, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

import subprocess
import shutil
import os
import glob
import time
from utils.utils import *

WATCHDOG_TIMEOUT = 3 # 3 seconds

this_file_path = os.path.dirname(os.path.abspath(__file__))
executable = os.path.join(this_file_path, 'Azure-Kinect-Sensor-SDK/build/bin/mrob_recorder')

p = None
path = None

app = FastAPI()

@app.get("/get_connected_camera_list")
def get_connected_camera_list():
    watchdog.reset()
    connected_camera_list = subprocess.check_output([f'{executable}', '--list']).decode('utf-8') # Get connected camera list
    return {"connected_camera_list": connected_camera_list}
    #return connected_camera_list

@app.post("/launch_recorder")
async def launch_recorder(data: dict):
    global path, p 

    file_base_name = data['file_base_name']

    path = os.path.join(this_file_path, 'records', file_base_name)
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)
    os.chdir(path)

    p = subprocess.Popen(data['cmd_line'].split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

@app.get("/get_info")
def get_info():
    watchdog.reset()
    data = {'mkv_file_size' : sizeof_fmt(os.path.getsize(glob.glob(os.path.join(path, '*.mkv'))[0])), 'recording_is_running' : p.poll() is None}
    return data

@app.get("/stop_recorder")
def stop_recorder():
    if p is not None:
        p.terminate()
    watchdog.stop()

watchdog = Watchdog(WATCHDOG_TIMEOUT, stop_recorder)
watchdog.stop()
