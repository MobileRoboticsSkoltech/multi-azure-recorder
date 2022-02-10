#!/usr/bin/env python3
import sys
import os
import signal
import subprocess
import collections
import time
import shutil
import json

# Recording parameters that updated during script
# gain???
cams = {#keys '1', '2', etc. correspond to the written numbers sticked to camera bodies
    '1' : {'ser_num' : '000583592412', 'master' : True , 'index' : None, 'sync_delay' : None, 'depth_mode' : 'NFOV_UNBINNED', 'color_mode' : '720p', 'frame_rate' : '30', 'exposure' : '2000', 'output_name' : None},
    '2' : {'ser_num' : '000905794612', 'master' : False, 'index' : None, 'sync_delay' : 360 , 'depth_mode' : 'NFOV_UNBINNED', 'color_mode' : '720p', 'frame_rate' : '30', 'exposure' : '2000', 'output_name' : None},
    #'3' : {'ser_num' : '000000000000', 'master' : False, 'index' : None, 'sync_delay' : 360 , 'resolution' : '720p', 'frame_rate' : '30', 'exposure' : '26000us', 'output_name' : None}
}

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
# Params: cams, 
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
master_cam_sticker = get_predefined_master_cam_sticker(cams)


# Parse predefined serial numbers
predef_ser_nums = [cams[cam_sticker]['ser_num'] for cam_sticker in cams.keys()]

# Get connected camera list
connected_camera_list = subprocess.check_output(['k4arecorder', '--list']).decode('utf-8')

# Get connected camera serial numbers and indexes
# Params: connected_camera_list
def get_connected_camera_serial_numbers_and_indexes(connected_camera_list):
    connected_indexes = []
    connected_ser_nums = []

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

    return connected_indexes, connected_ser_nums
# Return: connected_indexes, connected_ser_nums
connected_indexes, connected_ser_nums = get_connected_camera_serial_numbers_and_indexes(connected_camera_list)

# Assign indexes to predefined cameras
# Params: connected_ser_nums, connected_indexes, cams
def assign_indexes_to_predefined_cameras (connected_ser_nums, connected_indexes, cams):
    for connected_ser_num, connected_index in zip(connected_ser_nums, connected_indexes):
        for cam_sticker in cams.keys():
            if (cams[cam_sticker]['ser_num'] == connected_ser_num):
                cams[cam_sticker]['index'] = connected_index
    return cams
# Return: cams
cams = assign_indexes_to_predefined_cameras (connected_ser_nums, connected_indexes, cams)

# Prepare names for path and files
file_base_name = time.strftime("%Y-%m-%d-%H-%M-%S")
master_name = f'{master_cam_sticker}m.mkv'#f'{file_base_name}-{master_cam_sticker}m.mkv'

subordinate_name_template = lambda x : f'{x}s.mkv'#f'{file_base_name}-{x}s.mkv'

cams[master_cam_sticker]['output_name'] = master_name

for cam_sticker in cams.keys():
    if cam_sticker != master_cam_sticker:
        cams[cam_sticker]['output_name'] = subordinate_name_template(cam_sticker)

# Prepare command lines for recording
subordinate_cmd_lines = []

for cam_sticker in cams.keys():
    cc = cams[cam_sticker]
    index = cc['index']
    sync_delay = cc['sync_delay']
    depth_mode = cc['depth_mode']
    color_mode = cc['color_mode']
    frame_rate = cc['frame_rate']
    exposure = cc['exposure']
    output_name = cc['output_name']
    
    if cam_sticker == master_cam_sticker:
        master_cmd_line = f'k4arecorder --device {index} --external-sync Master --depth-mode {depth_mode} --color-mode {color_mode} --rate {frame_rate} --exposure-control {exposure} {output_name}'
        print_master('Master recording command:\n  ' + master_cmd_line)
    else:
        subordinate_cmd_line = f'k4arecorder --device {index} --external-sync Subordinate --sync-delay {sync_delay} --depth-mode {depth_mode} --color-mode {color_mode} --rate {frame_rate} --exposure-control {exposure} {output_name}'
        print_master('Subordinate recording command:\n  ' + subordinate_cmd_line)
        subordinate_cmd_lines.append(subordinate_cmd_line)

# Create path
path = os.path.join('records', file_base_name)
if os.path.exists(path):
    shutil.rmtree(path)
os.makedirs(path)
os.chdir(path)

# Save parameters dict
with open(f'{file_base_name}.json', 'w') as fp:
    json.dump(cams, fp)

# Launch recording
subordinate_processes = []
for subordinate_cmd_line in subordinate_cmd_lines:
    p = subprocess.Popen(subordinate_cmd_line.split())
    subordinate_processes.append(p)

time.sleep(1)

master_process = subprocess.Popen(master_cmd_line.split())

# Handle keyboard interrupt
try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    time.sleep(1)

#def main(args):
#	print ('kek')
#	result = subprocess.check_output(['k4arecorder', '--list'])
#	print(result.decode('utf-8'))#.stdout
#	pass

#if __name__ == '__main__':
#    main(sys.argv)