#!/usr/bin/env bash

#Usage: bash extractor input_directory output_directory

input_path="$1"
output_path="$2"

for mkv_path in $(find $input_path -name '*.mkv' | sed 's,.*/,,' | sed  's,.mkv,,');
	do

	mkdir -p $output_path/$mkv_path/{color,depth}

	cp $(find $input_path -name '*.json') $output_path/$(find $input_path -name '*.json' | sed 's,.*/,,')
	mv $output_path/$(find $input_path -name '*.json' | sed 's,.*/,,') $output_path/recording_params.json

	ffmpeg -i $input_path/$mkv_path'.mkv' -map 0:0 -vsync 0 $output_path/$mkv_path/color/%d.png
	ffmpeg -i $input_path/$mkv_path'.mkv' -map 0:1 -vsync 0 $output_path/$mkv_path/depth/%d.png

	mkvextract $input_path/$mkv_path'.mkv' timestamps_v2 3:$output_path/$mkv_path/imu.csv
	mkvextract $input_path/$mkv_path'.mkv' timestamps_v2 0:$output_path/$mkv_path/color_timestamps.csv 1:$output_path/$mkv_path/depth_timestamps.csv


	sed -i '1d' $output_path/$mkv_path/color_timestamps.csv
	N=1
	while read new_name;
		do
		mv $output_path/$mkv_path'/color/'$N'.png' $output_path/$mkv_path'/color/'$new_name'.png'
		((N++))   
		done < $output_path/$mkv_path/color_timestamps.csv;


	sed -i '1d' $output_path/$mkv_path/depth_timestamps.csv;
	N=1
	while read new_name
		do
		mv $output_path/$mkv_path'/depth/'$N'.png' $output_path/$mkv_path'/depth/'$new_name'.png'
		((N++))   
		done < $output_path/$mkv_path/depth_timestamps.csv;

	rm $output_path/$mkv_path/color_timestamps.csv $output_path/$mkv_path/depth_timestamps.csv
done
