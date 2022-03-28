#!/usr/bin/env bash

date=$(date '+%Y-%m-%d-%H-%M-%S')
./recorder.py --frame_rate 5 5 5 --output_path $date"_calib"