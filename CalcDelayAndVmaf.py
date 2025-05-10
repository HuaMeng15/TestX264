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

def calc_delay(result_dir):
    send_file = f'{result_dir}/send.log'
    receive_file = f'{result_dir}/receive.log'
    send_time = []
    read_data_from_file(send_file, 4, [send_time, [], [], []], ' ')
    receive_time = []
    read_data_from_file(receive_file, 5, [receive_time, [], [], [], []], ' ')
    delay = []
    for i in range(len(receive_time)):
        delay.append(int(receive_time[i]) - int(send_time[i + 1]))
    return delay

def read_json_file(rec_dir, vmaf_score_file):
    vmaf_score_json_file = f'{rec_dir}updated_recon_vmaf.json'
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

def calc_vmaf(result_dir, data):
    vmaf_score_file = f'{result_dir}vmaf_score.log'
    if os.path.exists(vmaf_score_file):
        os.remove(vmaf_score_file)
    
    send_video = f'input/{data}.mp4'
    os.system(f'cp {send_video} {result_dir}/send.mp4')

    vmaf_command = f'docker run --rm -v {result_dir}:/socket gfdavila/easyvmaf -r /socket/{result_dir}/send.mp4 -d /socket/{result_dir}/receive.mp4'
    os.system(vmaf_command)

    vmaf_scores = read_json_file(result_dir, vmaf_score_file)
    
    os.system(f'rm {result_dir}/send.mp4')
    
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
    parser.add_argument("--vbvRatio", type=float)
    parser.add_argument("--bitrate", type=str)
    parser.add_argument("--times", type=int)

    return parser.parse_args()

if __name__ == "__main__":
    cfg = parse_args()
    result_dir = f'result/{cfg.data}/{cfg.bitrate}/{cfg.vbvRatio}_{cfg.times}/'
    print(result_dir)
    delay_file = f'{result_dir}/delay.log'
    vmaf_file = f'{result_dir}/vmaf.log'
    every_trail_file = 'every_trail.csv'

    delay = calc_delay(result_dir)
    write_data_to_file([range(2, len(delay) + 1), delay], delay_file)
    delay = np.array(delay)
    avg_delay = np.mean(delay)
    
    vmaf = calc_vmaf(result_dir, cfg.data)
    write_data_to_file([range(1, len(vmaf)), vmaf], vmaf_file)
    vmaf = np.array(vmaf)
    avg_vmaf = np.mean(vmaf)
    
    f_every_trail = open(every_trail_file, 'a')
    f_every_trail.write(f'{cfg.data},{cfg.bitrate},{cfg.vbvRatio},{cfg.times},{avg_delay},{get_tail_result(delay, 0.9)},{avg_vmaf}\n')