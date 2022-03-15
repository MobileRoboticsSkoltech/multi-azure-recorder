# multi-azure-recorder
This repo contains tools for synchronized RGB+D data recording and extraction from multiple Azure Kinect DKs.


## Building
To start usage of the code, clone the repo with already modified Azure SDK:
```
git clone --recurse-submodules https://github.com/MobileRoboticsSkoltech/multi-azure-recorder
```

And follow the building process described in the official Azure Kinect DK API building instructions (__the root path there is Azure-Kinect-Sensor-SDK path__): [link](https://github.com/MobileRoboticsSkoltech/Azure-Kinect-Sensor-SDK/blob/e2d43f199956b3b40abd5d3a0d8eb6575699b9ae/docs/building.md). No additional actions are needed since our modifications are already implemented to the SDK. 

The following source paths and files are created in addition to original Azure code:  
```
Azure-Kinect-Sensor-SDK/tools:
  mrob_recorder                     # modified k4arecorder as a core executable for recorder.py
  mrob_imu_data_extractor           # IMU data extractor from MKV files as a backbone for extractor.sh
  mrob_timestamps_extractor         # timestamps data extractor from MKV files as a backbone for extractor.sh
  mrob_calibration_params_extractor # New! camera color and depth camera intrinsic and color-to-depth 
                                    # camera extrinsic calib params extractor as a backbone for extractor.sh
recorder.py                         # multi- mrob_recorder launcher for multiple cam recording
visualizer.py                       # online multi- RGB+D data stream visualizer
extractor.sh                        # MKV data extractor based on ffmpeg, mrob_imu_data_extractor, mrob_timestamps_extractor
```


## Recording
Recording process include synchronized data gathering from multiple Azure cameras. To start recording, launch
```
./recoder.py
```
with no arguments. For now, Camera parameters are predifined in a python dictionary, we plan to move the parameters to a separate file to avoid modification of the source code by mistake. The command-line arguments may be implemented sometime.

This is an example of the dict with camera params:
```
cams = {#keys '1', '2', etc. correspond to the written numbers sticked to camera bodies
    '1' : {'ser_num' : '000583592412', 'master' : True , 'index' : None, 'sync_delay' : None, 'depth_mode' : 'NFOV_UNBINNED', 'color_mode' : '720p', 'frame_rate' : '5', 'exposure' : '8000', 'output_name' : None},
    '2' : {'ser_num' : '000905794612', 'master' : False, 'index' : None, 'sync_delay' : 360 , 'depth_mode' : 'NFOV_UNBINNED', 'color_mode' : '720p', 'frame_rate' : '5', 'exposure' : '8000', 'output_name' : None}
}
```

### Recorded data structure
Files belonging to a single recording launch are stored in `records/` path. Their names contain date and time of the recrording start:
```
records/
  2022-02-10-08-36-51/
    1m.mkv
    2s.mkv
    3s.mkv
    ...
    recording_params.json
  2022-02-10-08-53-13/
    1m.mkv
    2s.mkv
    3s.mkv
    ...
    recording_params.json
  ...
```
Every path contains:
- multiple MKV files (every file correspond to a single cam, `1m` in a file name means "1st camera, Master", `2s` means "2nd camera, Subordinate") and 
- json dictionary with parameters of cameras (the majority of params are equal to python dict; however, has some updates for some values).  

Every recorded MKV file contains (if turned on in params)
- RGB video stream,
- D video stream,
- IMU data stream.

### Visualization during recording
`visualizer.py` is an additional tool for online image streams visualization. During recording, it can pool temporaly image files (jpg for RGB and binary for D image) created by `mrob_recorder` executable instance. It is not a part of `extractor.py`, but considered to be after solving some issues.

## Extraction
Extraction is aimed to
- extract RGB+D images from video streams,
- extract IMU data to a CSV file from IMU data stream,
- extract timestamps and name extracted images by timestamps,
- extract camera color and depth camera intrinsic and color-to-depth camera extrinsic calib params
from every MKV file.

To extract the data, launch the following script with the `<input path>` argument:
```
extractor.sh <input path> # For instance, 'extractor.sh records/2022-02-10-08-36-51'
```

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
