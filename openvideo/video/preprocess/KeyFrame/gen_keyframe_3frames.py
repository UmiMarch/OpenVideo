import os
import cv2
import math
import pathlib
import multiprocessing
from glob import glob
from tqdm import tqdm
from itertools import repeat
from multiprocessing import cpu_count, Process


def extract_keyframes_3frames(videos_dirs: str, sub_list: list):
    for dir in sub_list:
        print("dir: ",dir)
        for src_video_path in tqdm(glob(os.path.join(videos_dirs,dir, "*.mp4"))):
            folder = pathlib.Path(src_video_path).stem

            for video_path in glob(os.path.join(videos_dirs,dir,folder, "*.mp4")):

                output_dir = os.path.join(videos_dirs,dir,folder)
                cap = cv2.VideoCapture(video_path)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

                # Extract and save the first frame
                ret, first_frame = cap.read()
                if ret:
                    keyframe_name = f"{pathlib.Path(video_path).stem}_KeyFrame_1.jpg"
                    first_frame_path = os.path.join(output_dir, keyframe_name)
                    cv2.imwrite(first_frame_path, first_frame)

                # Extract and save the middle frame (rounded down if odd count)
                middle_frame_index = frame_count // 2
                cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame_index)
                ret, middle_frame = cap.read()
                if ret:
                    keyframe_name = f"{pathlib.Path(video_path).stem}_KeyFrame_2.jpg"
                    middle_frame_path = os.path.join(output_dir, keyframe_name)
                    cv2.imwrite(middle_frame_path, middle_frame)

                # Reset to the beginning and extract the last frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                cap.read()  # Skip first frame as we already have it
                for _ in range(frame_count - 2):  # Skip all frames until the last one
                    cap.read()

                ret, last_frame = cap.read()
                if ret:
                    keyframe_name = f"{pathlib.Path(video_path).stem}_KeyFrame_3.jpg"
                    last_frame_path = os.path.join(output_dir, keyframe_name)
                    cv2.imwrite(last_frame_path, last_frame)

                cap.release()


def get_video_files(directory: str):
    return [os.path.join(directory, f) for f in os.listdir(directory)]


def process_videos_parallel(directory: str, output_base_dir: str):
    video_files = get_video_files(directory)

    num_processes = cpu_count()
    with multiprocessing.Pool(num_processes) as pool:
        with tqdm(total=len(video_files), desc='Extracting Keyframes') as pbar:
            for _ in pool.imap_unordered(extract_keyframes_with_progress_update, zip(video_files, repeat(output_base_dir))):
                pbar.update(1)


def extract_keyframes_with_progress_update(video_path: str, output_base_dir: str):
    output_dir = os.path.join(output_base_dir, os.path.splitext(os.path.basename(video_path))[0])
    try:
        extract_keyframes_3frames(video_path, output_dir)
        return True  # Indicate success for tqdm update
    except Exception as e:
        print(f"Error processing video {video_path}: {e}")
        return False  # Indicate failure for tqdm update (not used here, but could be useful for logging)


def process_videos_parallel(videos_dirs: str):
    data_list = os.listdir(videos_dirs)
    n_processes = cpu_count()
    
    processes_list = []
    for n in range(n_processes):
        size = math.ceil(len(data_list) / n_processes)
        sub_list = data_list[n * size: min((n + 1) * size, len(data_list))]

        processes_list.append(Process(target=extract_keyframes_3frames, \
                                      args=(videos_dirs, \
                                            sub_list)))
    for p in processes_list:
        p.start()
    for p in processes_list:
        p.join()
