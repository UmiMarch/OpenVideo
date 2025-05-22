import os
import math
import shlex
import pathlib
import subprocess
import multiprocessing
from tqdm import tqdm
from glob import glob
from itertools import repeat
from multiprocessing import cpu_count, Process


def extract_keyframes_use_iframe(videos_dirs,sub_list):
    """
    Use FFmpeg extract frame I as keyframe。
    """

    for dir in sub_list:
        print("dir: ",dir)
        for src_video_path in tqdm(glob(os.path.join(videos_dirs,dir, "*.mp4"))):
            folder = pathlib.Path(src_video_path).stem

            for video_path in glob(os.path.join(videos_dirs,dir,folder, "*.mp4")):

                try:
                    prefix = f"{pathlib.Path(video_path).stem}_KeyFrame_I"
                    output_dir = os.path.join(videos_dirs, dir, folder)

                    command_template = (
                        'ffmpeg -i "{input_video}" '
                        '-hide_banner -loglevel panic '
                        '-vf "select=eq(pict_type\,PICT_TYPE_I)" '
                        '-vsync 2 "{output_prefix}_%d.jpg"'
                    )

                    command = command_template.format(
                        input_video=video_path,
                        output_prefix=os.path.join(output_dir, prefix),
                    )
                    # print(command)
                    subprocess.run(shlex.split(command), check=True)
                except Exception as e:
                    print(str(e))
                    continue



def get_video_files(directory):
    # return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(('.mp4', '.avi', '.mkv'))]
    return [os.path.join(directory, f) for f in os.listdir(directory)]

def process_videos_parallel(directory, output_base_dir):
    video_files = get_video_files(directory)

    num_processes = cpu_count()
    with multiprocessing.Pool(num_processes) as pool:
        with tqdm(total=len(video_files), desc='Extracting Keyframes') as pbar:
            for _ in pool.imap_unordered(extract_keyframes_with_progress_update, zip(video_files, repeat(output_base_dir))):
                pbar.update(1)

def extract_keyframes_with_progress_update(args):
    video_path, output_base_dir = args
    output_dir = os.path.join(output_base_dir, os.path.splitext(os.path.basename(video_path))[0])
    try:
        extract_keyframes_use_iframe(video_path, output_dir)
        return True  # Indicate success for tqdm update
    except Exception as e:
        print(f"Error processing video {video_path}: {e}")
        return False  # Indicate failure for tqdm update (not used here, but could be useful for logging)


def process_videos_parallel(videos_dirs):
    data_list = os.listdir(videos_dirs)
    n_processes = cpu_count()
    processes_list = []
    
    for n in range(n_processes):
        size = math.ceil(len(data_list) / n_processes)
        sub_list = data_list[n * size: min((n + 1) * size, len(data_list))]

        processes_list.append(Process(target=extract_keyframes_use_iframe, \
                                      args=(videos_dirs, \
                                            sub_list)))
    for p in processes_list:
        p.start()
    for p in processes_list:
        p.join()