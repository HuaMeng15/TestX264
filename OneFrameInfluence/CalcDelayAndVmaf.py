import argparse
import json
import os
from matplotlib import pyplot as plt
import numpy as np
import re
from math import log10, sqrt
import cv2

def read_data_from_file(file, count, data_lists, seperator):
    lines = open(file,'r').read().split('\n')
    for line in lines:
        line = line.split(seperator)
        if len(line) < count:
            continue
        for i in range(count):
            data_lists[i].append(line[i])

def write_data_to_file(data_lists, file):
    with open(file, 'w') as f_file:
        data_len = min([len(x) for x in data_lists])
        for i in range(data_len):
            content = ""
            for data in data_lists:
                content = content + str(data[i]) + ","
            content += "\n"
            f_file.write(content)

def read_bitrate_config(bitrate_file):
    bitrate_config = []
    lines = open(bitrate_file,'r').read().split('\n')
    for line in lines:
        line = line.split(',')
        if len(line) < 2:
            continue
        bitrate_config.append([int(line[0]), int(line[1])])
    return bitrate_config

def calc_delay(result_dir, bitrate_file, fps):
    send_file = f'{result_dir}send.log'
    delay_file = f'{result_dir}delay.log'
    bitrate_file = f'input/bitrate_config/{bitrate_file}'
    frame_sizes = []
    read_data_from_file(send_file, 3, [[], [], frame_sizes], ':')
    
    bitrate_config = read_bitrate_config(bitrate_file)
    print(bitrate_config)
    
    delay_list = []
    current_bitrate_index = 0
    transmitted_bytes_per_ms = bitrate_config[current_bitrate_index][1] / 8
    transmitted_bytes_per_ms /= 0.8
    current_bitrate_index += 1
    print(transmitted_bytes_per_ms)
    
    accumulated_time = 0
    one_frame_interval = int(1000 / fps)

    for i in range(1, len(frame_sizes)):
        frame_size = int(frame_sizes[i])
        if frame_size == 0:
            delay_list.append(accumulated_time)
            accumulated_time = max(0, accumulated_time - one_frame_interval)
            print(f'Frame {i + 1} is dropped, size: {frame_size}, accumulated_time: {accumulated_time}')
            continue
        if current_bitrate_index < len(bitrate_config) and \
          i == bitrate_config[current_bitrate_index][0]:
            transmitted_bytes_per_ms = bitrate_config[current_bitrate_index][1] / 8
            current_bitrate_index += 1
            print(i, transmitted_bytes_per_ms)
            
        send_frame_time = frame_size / transmitted_bytes_per_ms
        delay = send_frame_time + accumulated_time
        delay_list.append(delay)
        accumulated_time = max(0, delay - one_frame_interval)
        print(f'Frame {i + 1}: {frame_size} bytes, send_frame_time: {send_frame_time}, delay: {delay}, accumulated_time: {accumulated_time}')
    write_data_to_file([range(2, len(delay_list) + 2), delay_list], delay_file)
    write_data_to_file([range(2, len(frame_sizes)), frame_sizes[1:]], f'{result_dir}frame_size.log')
    return delay_list, frame_sizes

def read_json_file(rec_dir, vmaf_score_file):
    vmaf_score_json_file = f'{rec_dir}receive_vmaf.json'
    f_vmaf_score = open(vmaf_score_file, 'w')
    vmaf_scores = []

    with open(vmaf_score_json_file, 'r') as f:
        datas = json.load(f)
        vmaf_mean = datas['pooled_metrics']['vmaf']['mean']
        vmaf_harmonic_mean = datas['pooled_metrics']['vmaf']['harmonic_mean']
        for frame in datas['frames']:
            vmaf_scores.append(float(frame['metrics']['vmaf']))
    write_data_to_file([range(2, len(vmaf_scores) + 2), vmaf_scores], vmaf_score_file)
    return vmaf_scores

def extract_numbers(filename):
    match = re.search(r'_(\d+)x$', filename)
    if match:
        return int(match.group(1))
    else:
        return 1

def remove_speed_suffix(filename):
    cleaned_name = re.sub(r'_\d+x$', '', filename)
    return cleaned_name

def prepare_videos(result_dir, data, width, height, dropped_frames):
    speed = extract_numbers(data)
    print(f'Speed: {speed}')
    # speed = 1
    if speed != 1:
        data = remove_speed_suffix(data)
    send_raw_frames = f'input/{data}_raw_frames/'
    receive_raw_frames = f'{result_dir}receive_raw_frames/'
    print(receive_raw_frames)
    os.system("mkdir -p " + receive_raw_frames)
    receive_video = f'{result_dir}result.mkv'
    os.system(f'ffmpeg -i {receive_video} {receive_raw_frames}%d.png')
    
    receive_frame_cnt = len(os.listdir(receive_raw_frames))
    print(f'Receive frame count: {receive_frame_cnt}')
    count = 0
    
    one_by_one = False
    # one_by_one = True
    print(dropped_frames)
    # exit(0)
    
    if one_by_one:
        f_output_yuv = open(f'{result_dir}send.yuv', 'wb')
        for i in range(speed + 1, receive_frame_cnt * speed + 1 + len(dropped_frames), speed):
            send_img_path = send_raw_frames + str(i) + ".png"
            if i in dropped_frames:
                # send_img_path = send_raw_frames + str(i - 1) + ".png"
                continue
            print(f'Send image path: {send_img_path}')
            send_img = open(send_img_path, 'rb').read()
            f_output_yuv.write(send_img)
            count += 1
        print(f'Count: {count}')
        f_output_yuv.close()
        # exit(0)
        
        count = 0

        dropped_frame_number = 0
        f_output_yuv = open(f'{result_dir}receive.yuv', 'wb')
        for i in range(2, receive_frame_cnt + 1):
            rev_img_path = receive_raw_frames + str(i - dropped_frame_number) + ".png"
            if os.path.exists(rev_img_path) == False:
                print(f'Error: {rev_img_path} does not exist')
                continue
            print(f'Receive image path: {rev_img_path}')
            rev_img = open(rev_img_path, 'rb').read()
            f_output_yuv.write(rev_img)
            count += 1
        print(f'Count: {count}')
        f_output_yuv.close()
    else:
        f_output_yuv = open(f'{result_dir}send.yuv', 'wb')
        for i in range(speed + 1, receive_frame_cnt * speed + 1 + len(dropped_frames), speed):
            send_img_path = send_raw_frames + str(i) + ".png"
            # if i in dropped_frames:
            #     # send_img_path = send_raw_frames + str(i - 1) + ".png"
            #     continue
            # print(f'Send image path: {send_img_path}')
            if os.path.exists(send_img_path) == False:
                print(f'Error: {send_img_path} does not exist')
                continue
            send_img = open(send_img_path, 'rb').read()
            f_output_yuv.write(send_img)
            count += 1
        print(f'Count: {count}')
        f_output_yuv.close()

        count = 0

        dropped_frame_number = 0
        f_output_yuv = open(f'{result_dir}receive.yuv', 'wb')
        for i in range(2, receive_frame_cnt + 1 + len(dropped_frames)):
            if i in dropped_frames:
                dropped_frame_number += 1
            rev_img_path = receive_raw_frames + str(i - dropped_frame_number) + ".png"
            if os.path.exists(rev_img_path) == False:
                print(f'Error: {rev_img_path} does not exist')
                continue
            print(f'Receive image path: {rev_img_path}')
            rev_img = open(rev_img_path, 'rb').read()
            f_output_yuv.write(rev_img)
            count += 1
        print(f'Count: {count}')
        f_output_yuv.close()
    # exit(0)
    
    os.system(f'ffmpeg -s {width}x{height} -i {result_dir}receive.yuv -c:v libx264 -preset ultrafast -qp 0 -y {result_dir}receive.mp4')
    os.system(f'ffmpeg -s {width}x{height} -i {result_dir}send.yuv -c:v libx264 -preset ultrafast -qp 0 -y {result_dir}send.mp4')

def calc_vmaf(result_dir, data, width, height):
    vmaf_score_file = f'{result_dir}vmaf_score.log'
    if os.path.exists(vmaf_score_file):
        os.remove(vmaf_score_file)

    vmaf_command = f'docker run --rm -v {result_dir}:/socket gfdavila/easyvmaf -r /socket/send.mp4 -d /socket/receive.mp4'
    os.system(vmaf_command)

    vmaf_scores = read_json_file(result_dir, vmaf_score_file)
    
    os.system(f'rm {result_dir}receive.mp4')
    os.system(f'rm {result_dir}receive.yuv')
    os.system(f'rm {result_dir}send.mp4')
    os.system(f'rm {result_dir}send.yuv')
    return vmaf_scores

def PSNR(original, compressed): 
    mse = np.mean((original - compressed) ** 2) 
    if(mse == 0):  # MSE is zero means no noise is present in the signal . 
                  # Therefore PSNR have no importance. 
        return 100
    max_pixel = 255.0
    psnr = 20 * log10(max_pixel / sqrt(mse)) 
    return psnr

def calc_psnr(result_dir, data, width, height, dropped_frames):
    psnr_score_file = f'{result_dir}psnr_score.log'
    if os.path.exists(psnr_score_file):
        os.remove(psnr_score_file)

    speed = extract_numbers(data)
    print(f'Speed: {speed}')
    # speed = 1
    if speed != 1:
        data = remove_speed_suffix(data)
    send_raw_frames = f'input/{data}_raw_frames/'
    receive_raw_frames = f'{result_dir}receive_raw_frames/'
    if not os.path.exists(receive_raw_frames):
        os.system("mkdir -p " + receive_raw_frames)
        receive_video = f'{result_dir}result.mkv'
        os.system(f'ffmpeg -i {receive_video} {receive_raw_frames}%d.png')
    
    receive_frame_cnt = len(os.listdir(receive_raw_frames))
    
    psnr_scores = []
    
    drop_number = 0
    
    for i in range(2, receive_frame_cnt + 1 + len(dropped_frames)):
        send_img_path = send_raw_frames + str((i - 1) * speed + 1) + ".png"
        if i in dropped_frames:
            drop_number += 1
        rev_img_path = receive_raw_frames + str(i - drop_number) + ".png"
        if os.path.exists(send_img_path) == False or os.path.exists(rev_img_path) == False:
            print(f'Error: {send_img_path} or {rev_img_path} does not exist')
            continue
        # print(f'Send image path: {send_img_path}, Receive image path: {rev_img_path}')
        original = cv2.imread(send_img_path, 1)
        compressed = cv2.imread(rev_img_path, 1)
        value = PSNR(original, compressed)
        psnr_scores.append(value)
    
    write_data_to_file([range(2, receive_frame_cnt + 1), psnr_scores], psnr_score_file)

    return psnr_scores

def calc_vmaf_psnr(result_dir, data, width, height, dropped_frames):
    prepare_videos(result_dir, data, width, height, dropped_frames)

    vmaf_scores = calc_vmaf(result_dir, data, width, height)
    psnr_scores = calc_psnr(result_dir, data, width, height, dropped_frames)
    # exit(0)
    
    # os.system(f'rm -rf {result_dir}receive_raw_frames/')
    
    return vmaf_scores, psnr_scores

def get_tail_result(data, ratio):
    data.sort()
    data_len = len(data)
    tail_data = data[int(data_len * ratio):]
    mean_tail_data = np.mean(tail_data)
    return mean_tail_data

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str)
    parser.add_argument("--output_dir", type=str)
    parser.add_argument("--vbvRatio", type=float)
    parser.add_argument("--bitrate", type=str)
    parser.add_argument("--times", type=int)

    return parser.parse_args()

def extract_dropped_frames(result_dir):
    send_file = f'{result_dir}send.log'
    dropped_frames = []
    frame_sizes = []
    read_data_from_file(send_file, 3, [[], [], frame_sizes], ':')
    for i in range(1, len(frame_sizes)):
        frame_size = int(frame_sizes[i])
        if frame_size == 0:
            dropped_frames.append(i + 1)
    return dropped_frames

def draw_result(data, label, output_file):
    plt.figure(figsize=(5, 4))
    plt.plot(range(len(data)), data, color='blue')
    plt.xlabel('Frame Index')
    plt.ylabel(label)
    plt.grid()
    plt.savefig(output_file)
    plt.close()

def draw_slice_compare(data):
  traces = ['static_500kbps', 'static_1mbps', 'static_2mbps', 'static_5mbps', 'static_10mbps']
  for trace in traces:
    frame_sizes_no_divide = []
    frame_sizes_divide = []
    frame_sizes_byte_no_divide = []
    frame_sizes_byte_divide = []
    slice_number_no_divide = []
    slice_number_divide = []
    result_dir1 = f'/Users/menghua/Research/TestX264/result/slice/{data}/{trace}/slice_0/'
    result_dir2 = f'/Users/menghua/Research/TestX264/result/slice/{data}/{trace}/slice_1/'
    read_data_from_file(f'{result_dir1}original_frame_size.log', 4, [[], frame_sizes_byte_no_divide, frame_sizes_no_divide, slice_number_no_divide], ',')
    read_data_from_file(f'{result_dir2}original_frame_size.log', 4, [[], frame_sizes_byte_divide, frame_sizes_divide, slice_number_divide], ',')
    
    quality_no_divide = []
    quality_divide = []
    read_data_from_file(f'{result_dir1}vmaf_score.log', 2, [[], quality_no_divide], ',')
    read_data_from_file(f'{result_dir2}vmaf_score.log', 2, [[], quality_divide], ',')

    print(f'{data},{trace},{frame_sizes_byte_no_divide[0]},{quality_no_divide[0]},{frame_sizes_byte_divide[0]},{quality_divide[0]},{slice_number_divide[0]}')
    continue
    frame_sizes_no_divide = [float(i) for i in frame_sizes_no_divide][1:]
    frame_sizes_byte_no_divide = [float(i) for i in frame_sizes_byte_no_divide][1:]
    frame_sizes_divide = [float(i) for i in frame_sizes_divide][1:]
    frame_sizes_byte_divide = [float(i) for i in frame_sizes_byte_divide][1:]
    slice_number_no_divide = [int(i) for i in slice_number_no_divide][1:]
    slice_number_divide = [int(i) for i in slice_number_divide][1:]
    
    quality_no_divide = [float(i) for i in quality_no_divide][1:]
    quality_divide = [float(i) for i in quality_divide][1:]
    avg_quality_no_divide = np.mean(quality_no_divide)
    avg_quality_divide = np.mean(quality_divide)

    mean_no_divide = np.mean(frame_sizes_byte_no_divide)
    mean_divide = np.mean(frame_sizes_byte_divide)
    avg_slice_no_divide = np.mean(slice_number_no_divide)
    avg_slice_divide = np.mean(slice_number_divide)
    print(f'{data},{trace},{mean_no_divide:.2f},{avg_quality_no_divide:.2f},{avg_slice_no_divide:.2f},{mean_divide:.2f},{avg_quality_divide:.2f},{avg_slice_divide:.2f}')
    
    # print(f'Data: {data} Trace: {trace}, No divide mean frame size: {mean_no_divide:.2f} bytes, Divide mean frame size: {mean_divide:.2f} bytes')
    continue
    
    plt.figure(figsize=(8, 6))
    plt.rcParams.update({'font.size': 18})
    plt.plot(range(len(frame_sizes_divide)), frame_sizes_divide, color='orange', label='Multiple Slices')
    plt.plot(range(len(frame_sizes_no_divide)), frame_sizes_no_divide, color='blue', label='Single Slice')
    plt.xlabel('Frame Index')
    plt.ylabel('Frame Size (kbps)')
    plt.grid()
    plt.legend()
    plt.title(f'{trace}')
    plt.tight_layout()
    plt.savefig(f'/Users/menghua/Research/TestX264/{data}_{trace}_slice_compare.png')
    plt.close()

if __name__ == "__main__":
  print(f'Data,Trace,no_divide_avg_size,no_divide_avg_quality,no_divide_avg_slice_number,divide_avg_size,divide_avg_quality,divide_avg_slice_number')
  datas = ['Game_scene_change', 'Lecture']#, 'Vlog', 'Game', 'Sports']
  for data in datas:
      draw_slice_compare(data)
  exit(0)
  cfg = parse_args()
  result_dir = f'/Users/menghua/Research/TestX264/{cfg.output_dir}/'
  print(result_dir)
  every_trail_file = 'every_trail.csv'
  itmes = cfg.output_dir.split('/')
  if len(itmes) < 2:
      print("Error: output_dir format is wrong")
      exit(0)
  strategy = itmes[len(itmes) - 2]
  print(strategy)
  width = 1920
  height = 1080
  fps = 30
  start_index = 0
  end_index = 10000
  # start_index = 10
  # end_index = 50

  dropped_frames = extract_dropped_frames(result_dir)
  print(f'Dropped frames: {dropped_frames}')

  delay, frame_sizes = calc_delay(result_dir, cfg.bitrate, fps)
  vmaf, psnr = calc_vmaf_psnr(result_dir, cfg.data, width, height, dropped_frames)

  delay = []
  frame_sizes = []
  read_data_from_file(f'{result_dir}delay.log', 2, [[], delay], ',')
  read_data_from_file(f'{result_dir}frame_size.log', 2, [[], frame_sizes], ',')
  delay = [float(i) for i in delay]
  frame_sizes = [float(i) for i in frame_sizes]
  np_delay = np.array(delay)
  avg_delay = np.mean(np_delay[start_index:end_index])
  print(f'Average delay: {avg_delay} including head average: {np.mean(np_delay)}')
  # exit(0)
  
  vmaf = []
  read_data_from_file(f'{result_dir}vmaf_score.log', 2, [[], vmaf], ',')
  psnr = []
  read_data_from_file(f'{result_dir}psnr_score.log', 2, [[], psnr], ',')
  vmaf = [float(i) for i in vmaf]
  vmaf = np.array(vmaf)
  avg_vmaf = np.mean(vmaf[start_index:end_index])
  print(f'Average VMAF: {avg_vmaf} including head average: {np.mean(vmaf)}')

  psnr = [float(i) for i in psnr]
  psnr = np.array(psnr)
  avg_psnr = np.mean(psnr[start_index:end_index])
  print(f'Average PSNR: {avg_psnr} including head average: {np.mean(psnr)}')
  
  f_every_trail = open(every_trail_file, 'a')

  f_every_trail.write(f'{cfg.data},{cfg.bitrate},{strategy}_{start_index}_{end_index},{avg_delay},{get_tail_result(delay[start_index:end_index], 0.5)},{avg_vmaf},{avg_psnr}\n')
  
  draw_result(delay, 'Delay (ms)', f'{result_dir}delay.png')
  draw_result(vmaf, 'VMAF', f'{result_dir}vmaf.png')
  draw_result(frame_sizes, 'Frame Size', f'{result_dir}frame_size.png')
