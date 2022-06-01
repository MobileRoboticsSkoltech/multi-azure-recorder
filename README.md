# multi-azure-recorder
This repo contains tools for synchronized RGB+D data recording and extraction from multiple Azure Kinect DKs.


## Building
### Azure SDK
To start usage of the code, clone the repo with already modified Azure SDK:
```
git clone --recurse-submodules https://github.com/MobileRoboticsSkoltech/multi-azure-recorder
```

And follow the building process described in the official Azure Kinect DK API building instructions (__the root path there is Azure-Kinect-Sensor-SDK path__): [link](https://github.com/MobileRoboticsSkoltech/Azure-Kinect-Sensor-SDK/blob/e2d43f199956b3b40abd5d3a0d8eb6575699b9ae/docs/building.md).
In order to use the Azure Kinect SDK with the device and without being 'root', [this](https://github.com/MobileRoboticsSkoltech/Azure-Kinect-Sensor-SDK/blob/e2d43f199956b3b40abd5d3a0d8eb6575699b9ae/docs/usage.md#linux-device-setupshould) also must be done.
No additional actions are needed since our modifications are already implemented to the SDK. 

The following source paths and files are created in addition to original Azure code:  
```
Azure-Kinect-Sensor-SDK/tools:
  mrob_recorder                     # modified k4arecorder as a core executable for recorder.py
  mrob_images_extractor             # images extractor + undistorter + depth-to-color projector from MKV files as a backbone for extractor.sh
  mrob_imu_data_extractor           # IMU data extractor from MKV files as a backbone for extractor.sh
  mrob_timestamps_extractor         # timestamps data extractor from MKV files as a backbone for extractor.sh
  mrob_calibration_params_extractor # camera color and depth camera intrinsic and color-to-depth 
                                    # camera extrinsic calib params extractor as a backbone for extractor.sh
recorder.py                         # multi- mrob_recorder launcher for multiple cam recording
streamer.py                         # online multi- RGB+D data stream visualizer
extractor.sh                        # MKV data extractor based on ffmpeg, mrob_imu_data_extractor, mrob_timestamps_extractor
server.py                           # 
```
### RAM utilization
We use RAM folder for temporary data sharing instead of hard drive frequent read-write stress. For that, three steps must be performed (according to [askubuntu](https://askubuntu.com/questions/597268/virtual-ram-folder-in-ubuntu)).
1. Make the folder you want to mount the ram disk to (__must be `/mnt/mrob_tmpfs` everywhere__):
```
sudo mkdir /mnt/mrob_tmpfs
```
2. Create a ram disk. The size chosen to be 512MB, however can be decreased just in case.
```
sudo mount -t tmpfs -o size=512m tmpfs /mnt/mrob_tmpfs
```
3. Make mount permanent.
- open `/etc/fstab` in nano:
```
sudo nano /etc/fstab
```
- add the following line to that file and save the file:
```
tmpfs       /mnt/mrob_tmpfs tmpfs nodev,nosuid,noexec,nodiratime,size=512M   0 0
```

### Additional packages setup
#### ffmpef for extractor
The `ffmpeg` is also required for running extractor if `mrob_images_extractor` is not used as a backbone:
```shell
sudo apt-get install ffmpeg
```
#### python packages for streamer
For `streamer.py` `numpy`, `python3-tk`, `python3-pil`, `python3-pil.imagetk` packages are needed
```
sudo apt-get install python3-tk python3-pil python3-pil.imagetk python3-pip
pip3 install numpy
```
#### C++ OpenCV is needed
OpenCV is utilized for `mrob_images_extractor` backbine of `extractor.sh`.
Testing needed while building on a machine. Update this README too.

### (in case of problems) USB buffer increase
It is also can be needed to increase USB memory buffer. For that, use [this instruction](https://importgeek.wordpress.com/2017/02/26/increase-usbfs-memory-limit-in-ubuntu/).

### (in case of problems) Depth engine setup
We also found an issue with old OpenGL version when using Azure SDK (to be more precise, this problem comes from depth engine) on Ubuntu 18.04 with Intel integrated graphics. One of the solutions is [installing open source Mesa drivers](https://itsfoss.com/install-mesa-ubuntu/). But still, we are not sure if it is the best solution. With up-to-date Nvidia GPU drivers there should not be problems.

## Recording
Recording process include synchronized data gathering from multiple Azure cameras. To start recording from locally attached cameras, launch
```
./recoder.py
```
with no arguments. In this case, camera parameters are predifined by dict in `params.py`.

This is an example of the dict with camera params:
```
cams = {#keys '1', '2', etc. correspond to the written numbers sticked to camera bodies
    '1' : {'ser_num' : '000583592412', 'master' : True , 'index' : None, 'sync_delay' : None, 'depth_mode' : 'NFOV_UNBINNED', 'color_mode' : '720p', 'frame_rate' : '5', 'exposure' : '8000', 'output_name' : None, 'timestamps_table_filename' : None},
    '2' : {'ser_num' : '000905794612', 'master' : False, 'index' : None, 'sync_delay' : 360 , 'depth_mode' : 'NFOV_UNBINNED', 'color_mode' : '720p', 'frame_rate' : '5', 'exposure' : '8000', 'output_name' : None, 'timestamps_table_filename' : None}
}
```
In case of any specific parameters, `params.py` can be modified or command-line arguments can be put. 

### Recorded data structure
Files belonging to a single recording launch are stored in `records/` path. Their names contain date and time of the recrording start:
```
records/
├── 2022-02-10-08-36-51/
│   ├── 1m.mkv
│   ├── 2s.mkv
│   ├── 3s.mkv
│   ├── ...
│   ├── 1m.csv
│   ├── 2s.csv
│   ├── 3s.csv
│   ├── ...
│   └── recording_params.json
├── 2022-02-10-08-53-13/
│   ├── 1m.mkv
│   ├── 2s.mkv
│   ├── 3s.mkv
│   ├── ...
│   ├── 1m.csv
│   ├── 2s.csv
│   ├── 3s.csv
│   ├── ...
│   └── recording_params.json
...
```
Every path contains:
- multiple MKV files (every file correspond to a single cam, `1m` in a file name means "1st camera, Master", `2s` means "2nd camera, Subordinate"),
- multiple CSV files that stores matching of global and local image timestamps, and
- json dictionary with parameters of cameras (the majority of params are equal to python dict; however, has some updates for some values).  

Every recorded MKV file contains (if turned on in params)
- RGB video stream,
- D video stream,
- IMU data stream.

### Streaming during recording
`streamer.py` is an additional tool for online image streams visualization. During recording, it can pool temporaly image files (jpg for RGB and binary for D image) created by `mrob_recorder` executable instance. It is not a part of `extractor.py`, but considered to be after solving some issues.

## Extraction
Extraction is aimed to
- extract RGB+D images from video streams,
- extract IMU data to a CSV file from IMU data stream,
- extract timestamps and name extracted images by timestamps,
- extract camera color and depth camera intrinsic and color-to-depth camera extrinsic calib params
- undistort + and project depth to color when using `mrob_images_extractor` backbone in `extractor.sh`
from every MKV file.

To extract the data, launch the following script with the `<input path>` argument:
```
extractor.sh <input path> # For instance, 'extractor.sh records/2022-02-10-08-36-51'
```
To use `mrob_images_extractor` backbone, change `use_cpp_extractor=false` to `use_cpp_extractor=true` in `extractor.sh` file. For choosing extraction+undistortion+matching option, launch `mrob_images_extractor` with no arguments to get info TODO. 

### Output data structure
```
extracted-data/2022-03-03-17-14-36/
├── 1m
│   ├── color
│   │   ├── 000000391122.png
│   │   ├── 000000591066.png
│   │   ...
│   ├── depth
│   │   ├── 000000391066.png
│   │   ├── 000000591066.png
│   │   ...
│   ├── calib_params.json
│   ├── color_timestamps.csv
│   ├── depth_timestamps.csv
│   ├── ir_timestamps.csv
│   └── imu.csv
├── 2s
│   ├── color
│   │   ├── 000000189833.png
│   │   ├── 000000389800.png
│   │   ...
│   ├── depth
│   │   ├── 000000389755.png
│   │   ├── 000000589755.png
│   │   ...
│   ├── calib_params.json
│   ├── color_timestamps.csv
│   ├── depth_timestamps.csv
│   ├── ir_timestamps.csv
│   └── imu.csv
...
```
Every image name represents internal camera timestamp in <ins>__microseconds__</ins> from the start of every camera capturing process. Although, the timestamps do not belong to a common clock source, they are synchronized with sub-millisecond precision by Azure hardware by default. More info [here](https://box.zhores.net/index.php/s/93B2QYPxoBMS3aY?path=%2Fazures_timesync_analysis). Leading zeros are used in names for better visibility and sorting.
