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


LITERALS_DEFAULT = "def"
LITERALS_NONE = "none"


# Recording parameters that updated during script
# gain???
DEFAULT_PARAMS = {#keys '1', '2', etc. correspond to the written numbers sticked to camera bodies
    '1' : {'ser_num' : '000583592412', 'master' : True , 'index' : None, 'sync_delay' : None, 'depth_delay' : 0, 'depth_mode' : 'NFOV_UNBINNED', 'color_mode' : '720p', 'frame_rate' : 30, 'exposure' : 0, 'output_name' : None, 'timestamps_table_filename' : None},
    '2' : {'ser_num' : '000905794612', 'master' : False, 'index' : None, 'sync_delay' : 0   , 'depth_delay' : 0, 'depth_mode' : 'NFOV_UNBINNED', 'color_mode' : '720p', 'frame_rate' : 30, 'exposure' : 0, 'output_name' : None, 'timestamps_table_filename' : None},
    '9' : {'ser_num' : '000489713912', 'master' : False, 'index' : None, 'sync_delay' : 0   , 'depth_delay' : 0, 'depth_mode' : 'NFOV_UNBINNED', 'color_mode' : '720p', 'frame_rate' : 30, 'exposure' : -7, 'output_name' : None, 'timestamps_table_filename' : None}
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

    if master_cam_sticker is None:
        print_master_error('Master camera is not predifined')
        error_master_not_predefined = True

    if error_more_than_one_master | error_master_not_predefined:
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

        if cam_sticker == master_cam_sticker:
            master_cmd_line = f'{executable} --device {index} --external-sync Master --depth-delay {depth_delay} --depth-mode {depth_mode} --color-mode {color_mode} --rate {frame_rate} {exposure_setup} {output_name} {ts_table_filename}'
            print_master('Master recording command:\n  ' + master_cmd_line)
        else:
            subordinate_cmd_line = f'{executable} --device {index} --external-sync Subordinate --sync-delay {sync_delay} --depth-delay {depth_delay} --depth-mode {depth_mode} --color-mode {color_mode} --rate {frame_rate} {exposure_setup} {output_name} {ts_table_filename}'
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


def main():
    argument_parser = argparse.ArgumentParser("Recorder script")
    argument_parser.add_argument("--stickers", type=str, required=False, nargs="+")
    argument_parser.add_argument("--ser_num", type=str, required=False, nargs="+")
    argument_parser.add_argument("--master", type=bool_or_str_type, required=False, nargs="+")
    argument_parser.add_argument("--sync_delay", type=int_or_str_type, required=False, nargs="+")
    argument_parser.add_argument("--depth_delay", type=int_or_str_type, required=False, nargs="+")
    argument_parser.add_argument("--depth_mode", type=str, required=False, nargs="+")
    argument_parser.add_argument("--color_mode", type=str, required=False, nargs="+")
    argument_parser.add_argument("--frame_rate", type=int_or_str_type, required=False, nargs="+")
    argument_parser.add_argument("--exposure", type=int_or_str_type, required=False, nargs="+")
    argument_parser.add_argument("--output_path", type=str, required=False)
    args = argument_parser.parse_args()

    cams = process_arguments(vars(args))

    master_cam_sticker = get_predefined_master_cam_sticker(cams)
    predef_ser_nums = [cams[cam_sticker]['ser_num'] for cam_sticker in cams.keys()] # Parse predefined serial numbers
    connected_camera_list = subprocess.check_output([f'{executable}', '--list']).decode('utf-8') # Get connected camera list
    connected_ser_nums, connected_indexes = get_connected_camera_serial_numbers_and_indexes(connected_camera_list, predef_ser_nums)
    cams = assign_indexes_to_predefined_cameras (connected_ser_nums, connected_indexes, cams)
    cams, file_base_name = create_names_for_path_and_files(cams, master_cam_sticker, args.output_path)
    master_cmd_line, subordinate_cmd_lines = prepare_recording_command_lines(cams, master_cam_sticker)

    # Create path
    path = os.path.join('records', file_base_name)
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)
    os.chdir(path)

    # Save parameters dict
    with open('recording_params.json', 'w') as fp:
        json.dump(cams, fp)


    # Launch recording
    subordinate_processes = []
    for subordinate_cmd_line in subordinate_cmd_lines:
        p = subprocess.Popen(subordinate_cmd_line.split())
        subordinate_processes.append(p)

    # Wait till Subordinate cameras start before Master camera
    time.sleep(1)

    master_process = subprocess.Popen(master_cmd_line.split())

    # Handle keyboard interrupt
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        time.sleep(2) # needed to finalize stdouts before entire exit


if __name__ == '__main__':
    main()#sys.argv)
