# multi-azure-recorder
This repo contains tools for setup and record synchronized data streams from multiple Azure Kinect DKs

To clone the repo with already modified Azure SDK:
```
git clone --recurse-submodules https://github.com/MobileRoboticsSkoltech/multi-azure-recorder
```

## Installation
The installation process repeats the same one stated by the official Azure Kinect DK API: [link](https://github.com/MobileRoboticsSkoltech/Azure-Kinect-Sensor-SDK/blob/e2d43f199956b3b40abd5d3a0d8eb6575699b9ae/docs/building.md).  
No other installations are needed since the modified code is either contained in Azure repo or represents python or bash scripts.

The following source paths and files are created in addition to or in exchange of original Azure code:  
```
Azure-Kinect-Sensor-SDK/tools:
  mrob_recorder             # modified k4arecorder
  mrob_imu_data_extractor   # IMU data extractor from MKV files as a backbone for extractor.sh
  mrob_timestamps_extractor # timestamps data extractor from MKV files as a backbone for extractor.sh
recorder.py                 # multi- mrob_recorder launcher for multiple cam recording
visualizer.py               # online multi- RGB+D data stream visualizer
extractor.sh                # MKV data extractor based on ffmpeg, mrob_imu_data_extractor, mrob_timestamps_extractor
```

## Recording
`./recoder.py` - launch with no parameters. For now, camera params are stored in a python dictionary, this is an example of the dict:
```
cams = {#keys '1', '2', etc. correspond to the written numbers sticked to camera bodies
    '1' : {'ser_num' : '000583592412', 'master' : True , 'index' : None, 'sync_delay' : None, 'depth_mode' : 'NFOV_UNBINNED', 'color_mode' : '720p', 'frame_rate' : '5', 'exposure' : '8000', 'output_name' : None},
    '2' : {'ser_num' : '000905794612', 'master' : False, 'index' : None, 'sync_delay' : 360 , 'depth_mode' : 'NFOV_UNBINNED', 'color_mode' : '720p', 'frame_rate' : '5', 'exposure' : '8000', 'output_name' : None}
}
```

### Recorded data structure
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
Every path contains MKV files and json dict with parameters of cameras
`1m` means "1st camera, Master", `2s` means "2nd camera, Subordinate", 

## Extraction
```
extractor.sh <input path> # For instance, extractor.sh records/2022-02-10-08-36-51
```
### Output data structure
```
output/
  2022-02-10-08-36-51/
    1m/
      color/
        0001.png
        0002.png
        ...
      depth/
        0001.png
        0002.png
        ...
      imu.csv
    2s/
      color/
        0001.png
        0002.png
        ...
      depth/
        0001.png
        0002.png
        ...
      imu.csv
    recording_params.json
  ...  
```


