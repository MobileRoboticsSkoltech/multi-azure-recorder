#!/usr/bin/env bash

#Usage: bash extractor input_directory output_directory

if [ "$#" -ne 1 ]; then
    echo "Usage: extractor input_directory"
    exit
fi

#This block is to get exact path of the current script since internal structure of the repo path assumed to be constant
#and Azure tools are inside
SOURCE=${BASH_SOURCE[0]}
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR=$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )
  SOURCE=$(readlink "$SOURCE")
  [[ $SOURCE != /* ]] && SOURCE=$DIR/$SOURCE # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
DIR=$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )

TIMESTAMPS_EXTRACTOR_EXE="Azure-Kinect-Sensor-SDK/build/bin/mrob_timestamps_extractor"
IMU_DATA_EXTRACTOR_EXE="Azure-Kinect-Sensor-SDK/build/bin/mrob_imu_data_extractor"
CALIB_PARAMS_EXTRACTOR_EXE="Azure-Kinect-Sensor-SDK/build/bin/mrob_calibration_params_extractor"

input_path="$1"
output_path="$DIR/extracted-data/$(basename -- $1)"

rm -rf $output_path

for mkv_path in $(find $input_path -name '*.mkv' | sed 's,.*/,,' | sed  's,.mkv,,');
	do

	mkdir -p $output_path/$mkv_path/{color,depth}

	ffmpeg -i $input_path/$mkv_path'.mkv' -map 0:0 -vsync 0 $output_path/$mkv_path/color/%d.png
	ffmpeg -i $input_path/$mkv_path'.mkv' -map 0:1 -vsync 0 $output_path/$mkv_path/depth/%d.png
	#ffmpeg -i $input_path/$mkv_path'.mkv' -map 0:2 -vsync 0 $output_path/$mkv_path/ir/%d.png

	$TIMESTAMPS_EXTRACTOR_EXE   $input_path/$mkv_path'.mkv' $output_path/$mkv_path
	$IMU_DATA_EXTRACTOR_EXE     $input_path/$mkv_path'.mkv' $output_path/$mkv_path/imu.csv
	$CALIB_PARAMS_EXTRACTOR_EXE $input_path/$mkv_path'.mkv' $output_path/$mkv_path/calib_params.json
	sed -i '1d' $output_path/$mkv_path/color_timestamps.csv
	N=1
	while read new_name;
		do
		new_name_formatted=$(printf "%012d" $new_name)
		mv $output_path/$mkv_path'/color/'$N'.png' $output_path/$mkv_path'/color/'$new_name_formatted'.png'
		((N++))   
		done < $output_path/$mkv_path/color_timestamps.csv;


	sed -i '1d' $output_path/$mkv_path/depth_timestamps.csv;
	N=1
	while read new_name
		do
		new_name_formatted=$(printf "%012d" $new_name)
		mv $output_path/$mkv_path'/depth/'$N'.png' $output_path/$mkv_path'/depth/'$new_name_formatted'.png'
		((N++))   
		done < $output_path/$mkv_path/depth_timestamps.csv;

	#rm $output_path/$mkv_path/color_timestamps.csv $output_path/$mkv_path/depth_timestamps.csv
done
