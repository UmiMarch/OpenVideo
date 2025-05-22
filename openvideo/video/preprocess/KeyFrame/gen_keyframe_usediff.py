import os
import cv2
import argparse
import multiprocessing
from tqdm import tqdm
from itertools import repeat
from multiprocessing import cpu_count


def extract_keyframes_usediff(video_path, output_dir, image_diff_threshold=50, pixel_change_ratio_threshold = 0.3):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    cap = cv2.VideoCapture(video_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    first_keyframe_saved = False
    prev_frame = None

    for i in range(frame_count):
        ret, frame = cap.read()
        if not ret:
            break

        # Convert to grayscale for easier comparison
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if prev_frame is None:
            prev_frame = gray_frame
            continue

        # Compute absolute difference between current and previous frame
        diff = cv2.absdiff(gray_frame, prev_frame)

        # Threshold the difference image
        _, thresh = cv2.threshold(diff, image_diff_threshold, 255, cv2.THRESH_BINARY)

        # If the number of non-zero pixels (i.e., changed pixels) exceeds a certain percentage
        # of the total pixels, consider it a keyframe
        num_changed_pixels = cv2.countNonZero(thresh)
        frame_area = gray_frame.shape[0] * gray_frame.shape[1]
        pixel_change_ratio = num_changed_pixels / frame_area

        if pixel_change_ratio > pixel_change_ratio_threshold:  # Adjust this threshold as needed
            keyframe_index = i
            keyframe_name = f"{os.path.splitext(os.path.basename(video_path))[0]}_keyframe_{keyframe_index}.jpg"
            keyframe_path = os.path.join(output_dir, keyframe_name)
            cv2.imwrite(keyframe_path, frame)
            first_keyframe_saved = True

        prev_frame = gray_frame

    # Save the first frame as a keyframe if no other keyframes were found during the loop
    if not first_keyframe_saved:
        keyframe_index = 0
        keyframe_name = f"{os.path.splitext(os.path.basename(video_path))[0]}_keyframe_{keyframe_index}.jpg"
        keyframe_path = os.path.join(output_dir, keyframe_name)
        cv2.imwrite(keyframe_path, frame)

    cap.release()

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
        extract_keyframes_usediff(video_path, output_dir)
        return True  # Indicate success for tqdm update
    except Exception as e:
        print(f"Error processing video {video_path}: {e}")
        return False  # Indicate failure for tqdm update (not used here, but could be useful for logging)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="generate keyframe use diff")
    parser.add_argument("--input_video_dir", type=str, default=r'pexels-video')
    parser.add_argument("--output_keyframe_dir", type=str, default=r'pexels-video-keyframe')
    args = parser.parse_args()
    process_videos_parallel(args.input_video_dir, args.output_keyframe_dir)
    
# Usage:
# python gen_keyframe_usediff.py --input_video_dir input_video_dir --output_keyframe_dir output_keyframe_dir

