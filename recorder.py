#!/usr/bin/env python3
import sys
import os
import signal
import subprocess
import collections
import time
import shutil
import json
import argparse
import requests

from utils.utils import bcolors
from params import *

LITERALS_DEFAULT = "def"
LITERALS_NONE = "none"

TIMEOUT = 2

this_file_path = os.path.dirname(os.path.abspath(__file__))
executable = os.path.join(this_file_path, 'Azure-Kinect-Sensor-SDK/build/bin/mrob_recorder')

def print_master(*objects, sep=' ', end='\n', file=sys.stdout, flush=False, print_preword=True):
    print(bcolors.BOLD + bcolors.OKGREEN + ('MASTER MESSAGE: ' if print_preword else ''), end='', file=file, flush=flush)
    print(*objects, end='', file=file, flush=flush)
    print(bcolors.ENDC, sep=sep, end=end, file=file, flush=flush)

#def print_master(string):
#    print(bcolors.BOLD + bcolors.OKGREEN + 'MASTER MESSAGE: ' + string + bcolors.ENDC)

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

    if master_cam_sticker is None:
        print_master_error('Master camera is not predifined')
        error_master_not_predefined = True

    if error_more_than_one_master | error_master_not_predefined:
        print_master_error('Exit')
        sys.exit()
    return master_cam_sticker
# Return: master_cam_sticker

# Pull distributed connected camera list
# Params: cams
def get_distributed_connected_camera_list(cams):
    connected_camera_list = ''
    predef_addresses = [cams[cam_sticker]['address'] for cam_sticker in cams.keys()] # Parse predefined serial numbers
    predef_addresses = set(predef_addresses)
    for address in predef_addresses:
        response = requests.get(f'http://{address}get_connected_camera_list', stream=True)
        check_response(response, address)
        text = response.json()
        text = text['connected_camera_list']
        if 'No devices connected.' in text:
            print_master_error(f'No connected cameras in {address}. Exit')
            sys.exit()
        #if text.count('\n') > 1:
        #    print_master_error(f'More than one camera is connected to device with address {address}. Exit')
        #    sys.exit()
        connected_camera_list += text
    return connected_camera_list
# Return: connected_camera_list

# Get connected camera serial numbers and indexes
# Params: connected_camera_list, predef_ser_nums
def get_connected_camera_serial_numbers_and_indexes(connected_camera_list, predef_ser_nums):
    connected_ser_nums = []
    connected_indexes = []
    
    def get_val(line, pattern):
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
            
    error_not_connected = False        
    for predef_ser_num in predef_ser_nums:
        #if collections.Counter(connected_ser_nums) != collections.Counter(predef_ser_nums):
        if predef_ser_num not in connected_ser_nums:
            print_master_error(f'Predefined camera {predef_ser_num} is not connected')
            error_not_connected = True

    if error_not_recognized | error_not_connected:
        print_master_error('Exit')
        sys.exit()
    else:
        print_master('All required cameras are connected and recognized')

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
def create_names_for_path_and_files(cams, master_cam_sticker, output_path=None):
    if output_path is None:
        file_base_name = time.strftime("%Y-%m-%d-%H-%M-%S")
    else:
        file_base_name = output_path
    master_name = f'{master_cam_sticker}m.mkv'#f'{file_base_name}-{master_cam_sticker}m.mkv'
    ts_table_filename = f'{master_cam_sticker}m.csv'

    subordinate_name_template = lambda x : f'{x}s.mkv'#f'{file_base_name}-{x}s.mkv'
    subordinate_ts_table_filename_template = lambda x : f'{x}s.csv'#f'{file_base_name}-{x}s.mkv'

    cams[master_cam_sticker]['output_name'] = master_name
    cams[master_cam_sticker]['timestamps_table_filename'] = ts_table_filename

    for cam_sticker in cams.keys():
        if cam_sticker != master_cam_sticker:
            cams[cam_sticker]['output_name'] = subordinate_name_template(cam_sticker)
            cams[cam_sticker]['timestamps_table_filename'] = subordinate_ts_table_filename_template(cam_sticker)
    return cams, file_base_name
#Return: cams, file_base_name

# Prepare command lines for recording
# Params: cams, master_cam_sticker
def prepare_recording_command_lines(cams, master_cam_sticker):
    subordinate_cmd_lines = []
    subordinate_addresses = []

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
        stream_only = cc['stream_only']
        stream_only_setup = f'--save-all-captures {not stream_only}' if stream_only is not None else ''
        address = cc['address']

        if cam_sticker == master_cam_sticker:
            master_cmd_line = f'{executable} --device {index} --external-sync Master --depth-delay {depth_delay} --depth-mode {depth_mode} --color-mode {color_mode} --rate {frame_rate} {exposure_setup} {stream_only_setup} {output_name} {ts_table_filename}'
            master_address = address
            print_master('Master recording command:\n  ' + master_cmd_line)
        else:
            subordinate_cmd_line = f'{executable} --device {index} --external-sync Subordinate --sync-delay {sync_delay} --depth-delay {depth_delay} --depth-mode {depth_mode} --color-mode {color_mode} --rate {frame_rate} {exposure_setup} {stream_only_setup} {output_name} {ts_table_filename}'
            print_master('Subordinate recording command:\n  ' + subordinate_cmd_line)
            subordinate_cmd_lines.append(subordinate_cmd_line)
            subordinate_addresses.append(address)

    return master_cmd_line, subordinate_cmd_lines, master_address, subordinate_addresses
# Return: master_cmd_line, subordinate_cmd_lines, master_address, subordinate_addresses



def int_or_str_type(value):
    value = value.lower()
    if value != LITERALS_DEFAULT and value != LITERALS_NONE:
        return int(value)
    return value


def bool_or_str_type(value):
    value = value.lower()
    if value != LITERALS_DEFAULT and value != LITERALS_NONE:
        if value == "true":            
            return True 
        elif value == "false":
            return False
        else:
            print_master_error(f'CLI argument {value} is not recognized. Exit')
            sys.exit()
    return value

# Process camera parameters only
# Params: args
def process_arguments(args):
    # Use all cameras from default config or only specified cameras
    if args["stickers"] is not None:
        stickers = args["stickers"]
    else:
        stickers = DEFAULT_PARAMS.keys()

    cameras_params = {sticker: {} for sticker in stickers}

    for camera_sticker_idx, camera_sticker in enumerate(stickers):
        # Get possible parameters from default params
        for param_name, param_default_value in DEFAULT_PARAMS[camera_sticker].items():
            # If parameter was not specified in CLI or was specified as "default"
            if param_name not in args or args[param_name] is None or args[param_name][camera_sticker_idx] == LITERALS_DEFAULT:
                cameras_params[camera_sticker][param_name] = param_default_value
            # If parameter was specified as "none"
            elif args[param_name][camera_sticker_idx] == LITERALS_NONE:
                cameras_params[camera_sticker][param_name] = None
            # If parameter was specified as normal value
            else:
                cameras_params[camera_sticker][param_name] = args[param_name][camera_sticker_idx]

    return cameras_params
# Return: cameras_params

def check_response(x, address):
    if (x.status_code != 200):
        print_master_error(f'Response code from {address} is {x}. Exit')
        sys.exit()

def check_distributed_recording_status(address):
    response = requests.get(f'http://{address}get_recording_status', stream=True)
    check_response(response, address)
    data = response.json()
    for filename in data.keys():
        if not data[filename]['recording_is_running']:
            filename_ = filename.split('.')[0]
            print_master_error(f'Recording of camera {filename_} on address {address} is not running. Exit')
            sys.exit()
        print_master(f'{filename}:', data[filename]['mkv_file_size'], end=' ', print_preword=False)


def main():
    argument_parser = argparse.ArgumentParser("Recorder script")
    # These arguments below must be set up for every camera separately. For instance, "--stream_only true true false".
    argument_parser.add_argument("--stickers", type=str, required=False, nargs="+")
    argument_parser.add_argument("--ser_num", type=str, required=False, nargs="+")
    argument_parser.add_argument("--master", type=bool_or_str_type, required=False, nargs="+")
    argument_parser.add_argument("--sync_delay", type=int_or_str_type, required=False, nargs="+")
    argument_parser.add_argument("--depth_delay", type=int_or_str_type, required=False, nargs="+")
    argument_parser.add_argument("--depth_mode", type=str, required=False, nargs="+")
    argument_parser.add_argument("--color_mode", type=str, required=False, nargs="+")
    argument_parser.add_argument("--frame_rate", type=int_or_str_type, required=False, nargs="+")
    argument_parser.add_argument("--exposure", type=int_or_str_type, required=False, nargs="+")
    argument_parser.add_argument("--stream_only", type=bool_or_str_type, required=False, nargs="+")
    argument_parser.add_argument("--address", type=str, required=False, nargs="+")
    # These argumanets are single ones. For instance "--distributed true".
    argument_parser.add_argument("--output_path", type=str, required=False, nargs="+")
    argument_parser.add_argument("--distributed", type=bool_or_str_type, required=False)

    args = argument_parser.parse_args()

    cams = process_arguments(vars(args))

    master_cam_sticker = get_predefined_master_cam_sticker(cams)
    predef_ser_nums = [cams[cam_sticker]['ser_num'] for cam_sticker in cams.keys()] # Parse predefined serial numbers

    distributed = args.distributed
    if not distributed:
        connected_camera_list = subprocess.check_output([f'{executable}', '--list']).decode('utf-8') # Get connected camera list
    else:
        connected_camera_list = get_distributed_connected_camera_list(cams)
    connected_ser_nums, connected_indexes = get_connected_camera_serial_numbers_and_indexes(connected_camera_list, predef_ser_nums)

    cams = assign_indexes_to_predefined_cameras (connected_ser_nums, connected_indexes, cams)
    cams, file_base_name = create_names_for_path_and_files(cams, master_cam_sticker, args.output_path)
    master_cmd_line, subordinate_cmd_lines, master_address, subordinate_addresses = prepare_recording_command_lines(cams, master_cam_sticker)

    # Create path
    path = os.path.join('records', file_base_name)
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)
    os.chdir(path)

    # Save parameters dict
    with open('recording_params.json', 'w') as fp:
        json.dump(cams, fp)

    def launch_remote_recorder(address, cmd_line, file_base_name):
        data = {'cmd_line' : cmd_line, 'file_base_name' : file_base_name}
        response = requests.post(f'http://{address}launch_recorder', json=data, timeout=TIMEOUT)
        check_response(response, address)

    # Launch recording from Subordinate cameras
    if not distributed: 
        subordinate_processes = []
        for subordinate_cmd_line in subordinate_cmd_lines:
            p = subprocess.Popen(subordinate_cmd_line.split())
            subordinate_processes.append(p)
    else:
        for cmd_line, address in zip(subordinate_cmd_lines, subordinate_addresses):
            launch_remote_recorder(address, cmd_line, file_base_name)
            time.sleep(0.1)

    # Wait till Subordinate cameras start before Master camera
    time.sleep(1)

    if not distributed: 
        master_process = subprocess.Popen(master_cmd_line.split())
    else:
        launch_remote_recorder(master_address, master_cmd_line, file_base_name)

    addresses = set(subordinate_addresses + [master_address])

    # Handle keyboard interrupt
    print()
    count = 0
    try:
        while True:
            time.sleep(1)
            count+=1
            if distributed: 
                #print_master(count, end=' ')
                for address in addresses:
                    check_distributed_recording_status(address)
                print(end='\r')

    except KeyboardInterrupt:
        if distributed:
            for address in addresses:
                requests.get(f'http://{address}stop_recorder', stream=True, timeout=TIMEOUT)
            time.sleep(2)
        else:
            time.sleep(2) # needed to finalize stdouts before entire exit
        print()

if __name__ == '__main__':
    main()
