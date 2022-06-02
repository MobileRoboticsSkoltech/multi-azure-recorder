from fastapi import FastAPI, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, FileResponse


import subprocess
import shutil
import os
import glob
import time
import signal
from utils.utils import *

WATCHDOG_TIMEOUT = 10 # seconds
TEMP_IMAGES_PATH = '/mnt/mrob_tmpfs/images/'

this_file_path = os.path.dirname(os.path.abspath(__file__))
executable = os.path.join(this_file_path, 'Azure-Kinect-Sensor-SDK/build/bin/mrob_recorder')

processes = {}
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
    watchdog.reset()

    global path
    
    if os.path.exists(TEMP_IMAGES_PATH):
        shutil.rmtree(TEMP_IMAGES_PATH)
    os.makedirs(TEMP_IMAGES_PATH)
    
    file_base_name = data['file_base_name']

    path = os.path.join(this_file_path, 'records', file_base_name)
    if not os.path.exists(path):
        #shutil.rmtree(path)
        os.makedirs(path)
    os.chdir(path)

    arg_list = data['cmd_line'].split()
    arg_list.insert(0, executable)

    p = subprocess.Popen(arg_list)#, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    processes[arg_list[-2]] = p

@app.get("/get_recording_status")
def get_recording_status():
    watchdog.reset()
    data = {}
    for filename in processes.keys():
        mkv_path = os.path.join(path, filename)
        data[os.path.basename(mkv_path)] = {'mkv_file_size' : sizeof_fmt(os.path.getsize(mkv_path)), 'recording_is_running' : processes[filename].poll() is None}
    return data

@app.get("/stop_recorder")
def stop_recorder():
    watchdog.stop()
    for filename in processes.keys():
        p = processes[filename]
        if p is not None:
            p.send_signal(signal.SIGINT)



@app.get("/get_last_image")
def last_image():
    watchdog.reset()

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