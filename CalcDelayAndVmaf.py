import argparse
import json
import os
import numpy as np

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
    bitrate_file = f'input/bitrate_config/{bitrate_file}'
    frame_sizes = []
    read_data_from_file(send_file, 3, [[], [], frame_sizes], ':')
    
    bitrate_config = read_bitrate_config(bitrate_file)
    print(bitrate_config)
    
    delay_list = []
    current_bitrate_index = 0
    transmitted_bytes_per_ms = bitrate_config[current_bitrate_index][1] / 8
    current_bitrate_index += 1
    print(transmitted_bytes_per_ms)
    
    accumulated_time = 0
    one_frame_interval = int(1000 / fps)

    for i in range(0, len(frame_sizes) - 1):
        frame_size = int(frame_sizes[i])
        if current_bitrate_index < len(bitrate_config) and \
           i == bitrate_config[current_bitrate_index][0]:
            transmitted_bytes_per_ms = bitrate_config[current_bitrate_index][1] / 8
            current_bitrate_index += 1
            print(i, transmitted_bytes_per_ms)
            
        send_frame_time = frame_size / transmitted_bytes_per_ms
        delay = send_frame_time + accumulated_time
        delay_list.append(delay)
        
        accumulated_time = max(0, delay - one_frame_interval)
        print(f'Frame {i}: {frame_size} bytes, send_frame_time: {send_frame_time}, delay: {delay}, accumulated_time: {accumulated_time}')
    return delay_list

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
            f_vmaf_score.write(f"{frame['frameNum']},{frame['metrics']['vmaf']}\n")
        vmaf_scores = np.array(vmaf_scores)
    return vmaf_scores

def prepare_videos(result_dir, data, width, height):
    send_raw_frames = f'input/{data}_raw_frames/'
    receive_raw_frames = f'{result_dir}receive_raw_frames/'
    print(receive_raw_frames)
    os.system("mkdir -p " + receive_raw_frames)
    receive_video = f'{result_dir}result.mkv'
    os.system(f'ffmpeg -i {receive_video} {receive_raw_frames}%d.png')
    
    receive_frame_cnt = len(os.listdir(receive_raw_frames))

    f_output_yuv = open(f'{result_dir}send.yuv', 'wb')
    for i in range(2, receive_frame_cnt + 1):
        send_img_path = send_raw_frames + str(i) + ".png"
        send_img = open(send_img_path, 'rb').read()
        f_output_yuv.write(send_img)
    f_output_yuv.close()

    f_output_yuv = open(f'{result_dir}receive.yuv', 'wb')
    for i in range(2, receive_frame_cnt + 1):
        rev_img_path = receive_raw_frames + str(i) + ".png"
        rev_img = open(rev_img_path, 'rb').read()
        f_output_yuv.write(rev_img)
    f_output_yuv.close()
    
    os.system(f'ffmpeg -s {width}x{height} -i {result_dir}receive.yuv -c:v libx264 -preset ultrafast -qp 0 -y {result_dir}receive.mp4')
    os.system(f'ffmpeg -s {width}x{height} -i {result_dir}send.yuv -c:v libx264 -preset ultrafast -qp 0 -y {result_dir}send.mp4')

def calc_vmaf(result_dir, data, width, height):
    vmaf_score_file = f'{result_dir}vmaf_score.log'
    if os.path.exists(vmaf_score_file):
        os.remove(vmaf_score_file)
    
    prepare_videos(result_dir, data, width, height)

    vmaf_command = f'docker run --rm -v {result_dir}:/socket gfdavila/easyvmaf -r /socket/send.mp4 -d /socket/receive.mp4'
    os.system(vmaf_command)

    vmaf_scores = read_json_file(result_dir, vmaf_score_file)
    
    os.system(f'rm {result_dir}receive.mp4')
    os.system(f'rm {result_dir}receive.yuv')
    os.system(f'rm {result_dir}send.mp4')
    os.system(f'rm {result_dir}send.yuv')
    os.system(f'rm -rf {result_dir}receive_raw_frames/')
    
    return vmaf_scores

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

if __name__ == "__main__":
    cfg = parse_args()
    result_dir = f'/home/eceuser/menghua/Research/TestX264/{cfg.output_dir}'
    print(result_dir)
    delay_file = f'{result_dir}delay.log'
    vmaf_file = f'{result_dir}vmaf.log'
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

    delay = calc_delay(result_dir, cfg.bitrate, fps)
    write_data_to_file([range(2, len(delay) + 1), delay], delay_file)
    delay = np.array(delay)
    avg_delay = np.mean(delay)
    
    vmaf = calc_vmaf(result_dir, cfg.data, width, height)
    write_data_to_file([range(1, len(vmaf) + 1), vmaf], vmaf_file)
    vmaf = np.array(vmaf)
    avg_vmaf = np.mean(vmaf)
    
    f_every_trail = open(every_trail_file, 'a')
    f_every_trail.write(f'{cfg.data},{cfg.bitrate},{strategy},{cfg.times},{avg_delay},{get_tail_result(delay, 0.9)},{avg_vmaf}\n')