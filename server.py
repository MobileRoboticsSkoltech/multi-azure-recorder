from fastapi import FastAPI, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, FileResponse


import subprocess
import shutil
import os
import glob
import time
from utils.utils import *

WATCHDOG_TIMEOUT = 3 # 3 seconds
TEMP_IMAGES_PATH = '/mnt/mrob_tmpfs/images/'

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

    if os.path.exists(TEMP_IMAGES_PATH):
        shutil.rmtree(TEMP_IMAGES_PATH)
    os.makedirs(TEMP_IMAGES_PATH)
    
    file_base_name = data['file_base_name']

    path = os.path.join(this_file_path, 'records', file_base_name)
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)
    os.chdir(path)

    p = subprocess.Popen(data['cmd_line'].split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

@app.get("/get_recording_status")
def get_recording_status():
    watchdog.reset()
    data = {'mkv_file_size' : sizeof_fmt(os.path.getsize(glob.glob(os.path.join(path, '*.mkv'))[0])), 'recording_is_running' : p.poll() is None}
    return data

@app.get("/stop_recorder")
def stop_recorder():
    if p is not None:
        p.terminate()
    watchdog.stop()

@app.get("/get_last_image")
def last_image():
    images_path = glob.glob(os.path.join(TEMP_IMAGES_PATH, '*', 'color'))
    if len(images_path)==0:
        return
    images_path = images_path[0]

    images = glob.glob(os.path.join(images_path, '*'))
    if len(images)==0:
        return
    
    creation_times = [os.stat(image).st_ctime_ns for image in images]
    latest_creation_time = max(creation_times)
    latest_image = images[creation_times.index(latest_creation_time)]
    metainfo = ''
    for item in latest_image.split('/')[-3:-1]:
        metainfo += f'{item}_' 

    filename = f'{metainfo}{latest_creation_time}.jpg'
    return FileResponse(path=latest_image, filename=filename, media_type='image/jpeg')


watchdog = Watchdog(WATCHDOG_TIMEOUT, stop_recorder)
watchdog.stop()
