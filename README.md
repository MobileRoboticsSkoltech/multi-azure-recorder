# multi-azure-recorder
This repo contains tools for setup and record synchronized data streams from multiple Azure Kinect DKs

To clone modified Azure SDK too:
`git clone --recurse-submodules https://github.com/MobileRoboticsSkoltech/multi-azure-recorder`

## Installation
The installation process repeats the same one stated by the official Azure Kinect DK API.
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
`./recoder.py` - launch with no parameters. For now, setups are stored in a python dictionary, this is an example of the dict:
```
cams = {#keys '1', '2', etc. correspond to the written numbers sticked to camera bodies
    '1' : {'ser_num' : '000583592412', 'master' : True , 'index' : None, 'sync_delay' : None, 'depth_mode' : 'NFOV_UNBINNED', 'color_mode' : '720p', 'frame_rate' : '5', 'exposure' : '8000', 'output_name' : None},
    '2' : {'ser_num' : '000905794612', 'master' : False, 'index' : None, 'sync_delay' : 360 , 'depth_mode' : 'NFOV_UNBINNED', 'color_mode' : '720p', 'frame_rate' : '5', 'exposure' : '8000', 'output_name' : None}
}
```
## Extraction
`extractor.sh `
