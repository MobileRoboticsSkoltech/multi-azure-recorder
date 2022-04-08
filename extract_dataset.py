#!/usr/bin/env python3

import argparse
import csv
from lib2to3.pgen2.token import OP
from operator import mod
from pathlib import Path
from tkinter.messagebox import NO
from typing import Optional, List
import subprocess
import shutil

import pandas as pd
import numpy as np


MODE_EXTRACT_ONLY = "extract_only"
MODE_SORT_ONLY = "sort_only"
MODE_EXTRACT_AND_SORT = "extract_and_sort"

SET_POSIFIXES = ["__set_1__right", "__set_1__left", "__set_2__right", "__set_2__left", "__set_3__right", "__set_3__left",
                 "__set_4", "__set_5_move", "__set_5_rotate", "__set_5_zoom"]

CAMERAS = {"1m": "center", "2s": "right", "9s": "left"}
MODALITIES = ["color", "depth"]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", "-m", type=str, required=True, help="Operation mode")
    parser.add_argument("--input", "-i", type=str, required=True, help="Path to the input raw recordings")
    parser.add_argument("--output", "-o", type=str, required=True, help="Path to the extracted dataset root")
    parser.add_argument("--subjects", "-s", type=str, required=False, nargs="+", help="Subset of subjects (or folders) to extract from raw recordings")
    return parser.parse_args()


def do_extract_only_mode(args):
    raw_input_dir = Path(args.input)
    subject_dirs = find_subject_dirs(raw_input_dir, args.subjects)
    if len(subject_dirs) == 0:
        print("Valid subject dirs not found, exiting")
        return
    print("\nFollowing subject dirs will be processed:")
    for subject_dir in subject_dirs:
        print(f"{subject_dir}")
    
    output_root_dir = Path(args.output)

    for subject_dir in subject_dirs:
        process_subject_dir_extract_only(subject_dir, output_root_dir)


def find_subject_dirs(raw_input_dir: Path, subjects: Optional[str] = None) -> List[Path]:
    """
    Finds subject dirs by G* pattern or uses optional subjects list
    """
    assert raw_input_dir.is_dir(), "Input dir must exist!"
    if subjects is None:
        return sorted(raw_input_dir.glob("G*"))
    result = []
    for subject in subjects:
        subject_path = raw_input_dir / subject
        if not subject_path.is_dir():
            print(f"Dir {subject_path} does not exist, skipping")
            continue
        result.append(subject_path)
    return result


def process_subject_dir_extract_only(subject_dir: Path, output_root_dir: Path):
    print(f"\n    Processing {subject_dir}\n")
    gesture_set_dirs = []
    gesture_set_csvs = []
    for set_postfix in SET_POSIFIXES:
        match_dirs = sorted(subject_dir.glob(f"*{set_postfix}"))
        match_dirs = [e for e in match_dirs if e.is_dir()]
        match_csvs = sorted(subject_dir.glob(f"*{set_postfix}.csv"))
        match_csvs = [e for e in match_csvs if e.is_file()]
        if len(match_dirs) == 0:
            print(f"    Warning: no dirs found for set {set_postfix[2:]}")
        else:
            gesture_set_dirs = gesture_set_dirs + match_dirs
            gesture_set_csvs = gesture_set_csvs + match_csvs
    
    print("\n    Following record dirs will be extracted:")
    for record_dir in gesture_set_dirs:
        print(f"\n    {record_dir}")

    output_subject_dir = output_root_dir / subject_dir.name
    output_subject_dir.mkdir(parents=True, exist_ok=True)
    for record_dir in gesture_set_dirs:
        extract_record(record_dir, output_subject_dir)

    print("\n    Copying CSV files")
    for csv_file in gesture_set_csvs:
        shutil.copy(str(csv_file), str(output_subject_dir / csv_file.name))

    print(f"\n    Finsihed processing {subject_dir}\n")


def extract_record(record_dir: Path, extraction_output_dir: Path):
    print(f"\n        Extracting {record_dir} to {extraction_output_dir}")
    p = subprocess.Popen(f"./extractor.sh {record_dir} {extraction_output_dir}", shell=True)
    p.wait()
    for camera in CAMERAS.keys():
        csv_file_name = camera + ".csv"
        shutil.copy(str(record_dir / csv_file_name), str(extraction_output_dir / record_dir.name / camera / csv_file_name))


def do_sort_only_mode(args):
    extracted_input_dir = Path(args.input)
    subject_dirs = find_subject_dirs(extracted_input_dir, args.subjects)
    if len(subject_dirs) == 0:
        print("Valid subject dirs not found, exiting")
        return
    print("\nFollowing subject dirs will be processed:")
    for subject_dir in subject_dirs:
        print(f"{subject_dir}")
    
    output_root_dir = Path(args.output)

    for subject_dir in subject_dirs:
        process_subject_dir_sort_only(subject_dir, output_root_dir)


def process_subject_dir_sort_only(subject_dir: Path, output_root_dir: Path):
    print(f"\n    Processing {subject_dir}\n")
    subject_output_dir = output_root_dir / subject_dir.name
    gesture_sets = {}
    for set_postfix in SET_POSIFIXES:
        postfix_sets = sorted(subject_dir.glob(f"*{set_postfix}"))
        postfix_sets = [e for e in postfix_sets if e.is_dir()]
        gesture_sets[set_postfix] = postfix_sets

    for set_postfix, postfix_sets  in gesture_sets.items():
        trial_offset = 0
        for gesture_set in postfix_sets:
            trial_offset += sort_gesture_set(gesture_set.name, subject_dir, subject_output_dir, trial_offset)


def sort_gesture_set(gesture_set: str, subject_dir: Path, subject_output_dir: Path, trial_offset: int) -> int:
    print(f"\n        Processing {gesture_set}")
    parts = gesture_set.split("__")
    csv_name = parts[0] + "__pres__" + "__".join(parts[1:])
    gesture_set_df = pd.read_csv(str(subject_dir / (csv_name + ".csv")))
    
    if "left" in parts:
        hand = "left"
    elif "right" in parts:
        hand = "right"
    else:
        hand = "both"
    
    n_trials = 0

    for camera in CAMERAS.keys():
        print(f"\n        Camera {camera} ({CAMERAS[camera]})")
        for modality in MODALITIES:
            print(f"        Modality {modality}")
            for idx in reversed(gesture_set_df.index):
                gesture_name = gesture_set_df.loc[idx, "gesture"]
                t0 = gesture_set_df.loc[idx, "t0_1"]
                t1 = gesture_set_df.loc[idx, "t1_1"]
                trial = gesture_set_df.loc[idx, "trial"]
                if trial > n_trials:
                    n_trials = trial
                is_bad = gesture_set_df.loc[idx, "is_bad"]
                sort_camera_modality_frames(subject_dir / gesture_set, subject_output_dir, gesture_name, hand,
                                            t0, t1, trial, is_bad, camera, modality, trial_offset)
        
    return n_trials


def sort_camera_modality_frames(gesture_set_dir: Path, subject_output_dir: Path, gesture_name: str, hand: str,
                                t0: int, t1: int, trial: int, is_bad: bool,
                                camera: str, modality: str, trial_offset: int) -> int:
    trial_output_dir = subject_output_dir / gesture_name / hand / f"trial{trial + trial_offset}"
    trial_output_dir.mkdir(parents=True, exist_ok=True)
    frames_output_dir = trial_output_dir / CAMERAS[camera] / modality
    frames_output_dir.mkdir(parents=True, exist_ok=True)

    frames_dir = gesture_set_dir / camera / modality
    frames = [e.name.split(".")[0] for e in sorted(frames_dir.glob("*.png"))]

    camera_timestamps_df = pd.read_csv(str(gesture_set_dir / camera / (camera + ".csv")))
    t0_us = None
    t1_us = None
    for _, row in camera_timestamps_df.iterrows():
        camera_t = row[modality + "_ts_us"]
        global_t = row["global_ts_us"]
        if global_t >= t0 and t0_us is None:
            t0_us = camera_t
        if global_t >= t1 and t1_us is None:
            t1_us = camera_t
    
    start_frame_idx = None
    end_frame_idx = None
    for i in range(len(frames)):
        if int(frames[i]) >= t0_us and start_frame_idx is None:
            start_frame_idx = i
        if int(frames[i]) >= t1_us and end_frame_idx is None:
            end_frame_idx = i
    
    gesture_frames = frames[start_frame_idx:(end_frame_idx + 1)]
    fps = int(round(len(gesture_frames) / ((t1_us - t0_us) * 1e-6), 0))
    print(f"                Gesture: {gesture_name}" + \
          f"                Trial: {trial}" + \
          f"                Length: {len(gesture_frames)}",
          f"                FPS: {fps}")
    # print(f"            Gest: {gesture_name}, trial: {trial} Len: {len(gesture_frames)}, first: {first_frame_idx}, last: {last_frame_idx}, offset: {last_frame_offset}")

    for gesture_frame in gesture_frames:
        frame_file = gesture_frame + ".png"
        shutil.copy(str(frames_dir / frame_file), str(frames_output_dir / frame_file))
    
    is_bad_mark_file = trial_output_dir / ("bad" if is_bad else "good")
    is_bad_mark_file.touch(exist_ok=True)


def main():
    args = parse_args()

    if args.mode == MODE_EXTRACT_ONLY:
        do_extract_only_mode(args)
    elif args.mode == MODE_SORT_ONLY:
        do_sort_only_mode(args)
    elif args.mode == MODE_EXTRACT_AND_SORT:
        raise NotImplementedError()
    else:
        raise RuntimeError("Unknown operation mode")


if __name__ == "__main__":
    main()
