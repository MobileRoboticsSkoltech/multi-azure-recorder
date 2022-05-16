#!/usr/bin/env python3
import sys
import os
import signal
import subprocess
import collections
import time
import shutil
import json
import io
import argparse
from fastapi import FastAPI
from PIL import Image
from fastapi.responses import StreamingResponse

LITERALS_DEFAULT = "def"
LITERALS_NONE = "none"

app = FastAPI()

# Recording parameters that updated during script
# gain???
DEFAULT_PARAMS = {#keys '1', '2', etc. correspond to the written numbers sticked to camera bodies
    '3' : {'ser_num' : '000589692912', 'master' : True , 'index' : None, 'sync_delay' : None, 'depth_delay' : 0, 'depth_mode' : 'NFOV_UNBINNED', 'color_mode' : '720p', 'frame_rate' : 30, 'exposure' : -7, 'output_name' : None, 'timestamps_table_filename' : None},
    '5' : {'ser_num' : '000230292412', 'master' : False, 'index' : None, 'sync_delay' : 0   , 'depth_delay' : 0, 'depth_mode' : 'NFOV_UNBINNED', 'color_mode' : '720p', 'frame_rate' : 30, 'exposure' : -7, 'output_name' : None, 'timestamps_table_filename' : None},
}

this_file_path = os.path.dirname(os.path.abspath(__file__))
executable = os.path.join(this_file_path, 'Azure-Kinect-Sensor-SDK/build/bin/mrob_recorder')

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_master(string):
    print(bcolors.BOLD + bcolors.OKGREEN + 'MASTER MESSAGE: ' + string + bcolors.ENDC)

def print_master_error(string):
    print(bcolors.BOLD + bcolors.FAIL + 'MASTER ERROR: ' + string + bcolors.ENDC)

# Check master camera setup
# Params: cams
def get_predefined_master_cam_sticker(cams):
    master_cam_sticker = None
    master_cam_already_found = False
    error_master_not_predefined = False
    error_more_than_one_master = False
    for cam_sticker in cams.keys():
        if (cams[cam_sticker]['master'] == True):
            print_master(f'Camera with sticker {cam_sticker} is predifined as a Master camera')
            master_cam_sticker = cam_sticker
            if master_cam_already_found == True:
                print_master_error('More than one camera is predifined as a Master camera')
                error_more_than_one_master = True
            master_cam_already_found = True

    if error_more_than_one_master:
        print_master_error('Exit')
        sys.exit()
    return master_cam_sticker
# Return: master_cam_sticker

# Get connected camera serial numbers and indexes
# Params: connected_camera_list, predef_ser_nums
def get_connected_camera_serial_numbers_and_indexes(connected_camera_list, predef_ser_nums):
    connected_ser_nums = []
    connected_indexes = []

    def get_val(line, pattern):
        print(line, pattern)
        return line.split(pattern)[1].split()[0]

    error_not_recognized = False
    for line in connected_camera_list.split(sep='\n'):
        if line == 'No devices connected.':
            print_master_error('No devices connected.\nExit')
            sys.exit()
        if len(line) > 0:
            ser_num = get_val(line, 'Serial:')
            print_master(f'Found camera with serial number {ser_num}')
            if ser_num not in predef_ser_nums:
                print_master_error(f'Connected camera {ser_num} is not recognized')
                error_not_recognized = True

            index = get_val(line, 'Index:')
            
            connected_ser_nums.append(ser_num)
            connected_indexes.append(index)
            
    return connected_ser_nums, connected_indexes
# Return: connected_ser_nums, connected_indexes

# Assign indexes to predefined cameras
# Params: connected_ser_nums, connected_indexes, cams
def assign_indexes_to_predefined_cameras (connected_ser_nums, connected_indexes, cams):
    for connected_ser_num, connected_index in zip(connected_ser_nums, connected_indexes):
        for cam_sticker in cams.keys():
            if (cams[cam_sticker]['ser_num'] == connected_ser_num):
                cams[cam_sticker]['index'] = connected_index
    return cams
# Return: cams

# Prepare names for path and files
# Params: master_cam_sticker, cams
def create_names_for_path_and_files(cams, master_cam_sticker=None, output_path=None):
    
    if master_cam_sticker is not None:
        master_name = f'{master_cam_sticker}m.mkv'#f'{file_base_name}-{master_cam_sticker}m.mkv'
        ts_table_filename = f'{master_cam_sticker}m.csv'
        
        cams[master_cam_sticker]['output_name'] = master_name
        cams[master_cam_sticker]['timestamps_table_filename'] = ts_table_filename

    subordinate_name_template = lambda x : f'{x}s.mkv'#f'{file_base_name}-{x}s.mkv'
    subordinate_ts_table_filename_template = lambda x : f'{x}s.csv'#f'{file_base_name}-{x}s.mkv'

    for cam_sticker in cams.keys():
        if cam_sticker != master_cam_sticker:
            cams[cam_sticker]['output_name'] = subordinate_name_template(cam_sticker)
            cams[cam_sticker]['timestamps_table_filename'] = subordinate_ts_table_filename_template(cam_sticker)
    return cams
#Return: cams, file_base_name

# Prepare command lines for recording
# Params: cams, master_cam_sticker
def prepare_recording_command_lines(cams, master_cam_sticker, tracking_flag=False, fisheye_flag=False):
    subordinate_cmd_lines = []
    master_cmd_line = None

    for cam_sticker in cams.keys():
        cc = cams[cam_sticker]
        index = cc['index']
        sync_delay = cc['sync_delay']
        depth_delay = cc['depth_delay']
        depth_mode = cc['depth_mode']
        color_mode = cc['color_mode']
        frame_rate = cc['frame_rate']
        exposure = cc['exposure']
        output_name = cc['output_name']
        exposure_setup = f'--exposure-control {exposure}' if exposure is not None else ''
        ts_table_filename = cc['timestamps_table_filename']

        tracking_flag='off'
        fisheye_flag='off'

        if cam_sticker == master_cam_sticker:
            master_cmd_line = f'{executable} --device {index} --tracking {tracking_flag} --fisheye {fisheye_flag} --external-sync Master --depth-delay {depth_delay} --depth-mode {depth_mode} --color-mode {color_mode} --rate {frame_rate} {exposure_setup} {output_name} {ts_table_filename}'
            print_master('Master recording command:\n  ' + master_cmd_line)
        else:
            subordinate_cmd_line = f'{executable} --device {index} --tracking {tracking_flag} --fisheye {fisheye_flag} --external-sync Subordinate --sync-delay {sync_delay} --depth-delay {depth_delay} --depth-mode {depth_mode} --color-mode {color_mode} --rate {frame_rate} {exposure_setup} {output_name} {ts_table_filename}'
            print_master('Subordinate recording command:\n  ' + subordinate_cmd_line)
            subordinate_cmd_lines.append(subordinate_cmd_line)
    return master_cmd_line, subordinate_cmd_lines
# Return: master_cmd_line, subordinate_cmd_lines


def int_or_str_type(value):
    value = value.lower()
    if value != LITERALS_DEFAULT and value != LITERALS_NONE:
        return int(value)
    return value


def bool_or_str_type(value):
    value = value.lower()
    if value != LITERALS_DEFAULT and value != LITERALS_NONE:
        return True if value == "true" else False
    return value


def process_arguments():
    # Use all cameras from default config or only specified cameras
    stickers = DEFAULT_PARAMS.keys()

    cameras_params = {sticker: {} for sticker in stickers}

    for camera_sticker_idx, camera_sticker in enumerate(stickers):
        # Get possible parameters from default params
        for param_name, param_default_value in DEFAULT_PARAMS[camera_sticker].items():
            # If parameter was not specified in CLI or was specified as "default"
            cameras_params[camera_sticker][param_name] = param_default_value
            
    return cameras_params

processes = []
current_path = ''
is_tracking = False

@app.get("/start")
def start(fname: str = '', fish: str = 'off'):
    global processes, current_path, is_tracking
    if fname == '': fname = time.strftime("%Y-%m-%d-%H-%M-%S")
    if len(processes) > 0: return
    
    cams = process_arguments()

    root_dir = os.getcwd()

    master_cam_sticker = get_predefined_master_cam_sticker(cams)
    predef_ser_nums = [cams[cam_sticker]['ser_num'] for cam_sticker in cams.keys()] # Parse predefined serial numbers
    try:
        connected_camera_list = subprocess.check_output([f'{executable}', '--list']).decode('utf-8') # Get connected camera list
        connected_ser_nums, connected_indexes = get_connected_camera_serial_numbers_and_indexes(connected_camera_list, predef_ser_nums)
        is_tracking = False
    except:
        is_tracking = True
    
    # Create path
    path = os.path.join('../records', fname)
    current_path = path
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)
    os.chdir(path)
    
    if not is_tracking:
        cams = assign_indexes_to_predefined_cameras (connected_ser_nums, connected_indexes, cams)
        cams = create_names_for_path_and_files(cams, master_cam_sticker)
        master_cmd_line, subordinate_cmd_lines = prepare_recording_command_lines(cams, master_cam_sticker)
        
        if os.path.exists('color_preview'):
            shutil.rmtree('color_preview')
        os.makedirs('color_preview')
        
        # Save parameters dict
        with open('recording_params.json', 'w') as fp:
            json.dump(cams, fp)
    else:
        master_cmd_line = f'/home/telezhka/robot/Azure-Kinect-Sensor-SDK/build/bin/k4arecorder -a off -t on -f {fish}'
        subordinate_cmd_lines = []

    for subordinate_cmd_line in subordinate_cmd_lines:
        p = subprocess.Popen(subordinate_cmd_line.split())
        processes.append(p)

    # Wait till Subordinate cameras start before Master camera
    time.sleep(1)

    if master_cmd_line is not None: processes.append(subprocess.Popen(master_cmd_line.split()))

    os.chdir(root_dir)

@app.get("/stop")
def stop():
    global processes
    for p in processes:
        p.terminate()
    processes = []
    print('Recording stopped')
    
@app.get("/remove")
def stop(fname: str = ''):
    try:
        shutil.rmtree(f'../records/{fname}')
        print(f'{fname} removed')
    except OSError as e:
        print ("Error: %s - %s." % (e.filename, e.strerror))
    
@app.get("/preview")
def preview():
    global current_path, is_tracking
    
    if (is_tracking):
        files = sorted([f for f in os.listdir(os.path.join(current_path)) if '.jpg' in f])
    else:
        files = sorted([f for f in os.listdir(os.path.join(current_path, 'color_preview')) if '.jpg' in f])
        if len(files) > 2:
            for i in range(len(files) - 2):
                os.remove(os.path.join(current_path, 'color_preview', files[i]))
    if (len(files) == 0): return
    fname = files[-1]
    if (is_tracking): image = Image.open(os.path.join(current_path, fname))
    else: image = Image.open(os.path.join(current_path, 'color_preview', fname))
    # create a thumbnail image
    # image.thumbnail((400, 400))
    imgio = io.BytesIO()
    image.save(imgio, 'JPEG')
    imgio.seek(0)
    return StreamingResponse(content=imgio, media_type="image/jpeg")
