import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np
import os

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

def CalculateDelay(result_dir, bitrate_indexes, network_bandwidths, response_time, fps=30):
    send_file = f'{result_dir}send.log'
    frame_sizes = []
    read_data_from_file(send_file, 3, [[], [], frame_sizes], ':')
    
    delay = []
    
    current_bitrate_index = 0
    transmitted_bytes_per_ms = int(network_bandwidths[current_bitrate_index]) / 8
    current_bitrate_index += 1
    
    accumulated_time = 0
    one_frame_interval = int(1000 / fps)
    
    for i in range(len(frame_sizes)):
        frame_size = int(frame_sizes[i])
        if current_bitrate_index < len(bitrate_indexes) and \
           i == (int(bitrate_indexes[current_bitrate_index]) - response_time):
            transmitted_bytes_per_ms = int(network_bandwidths[current_bitrate_index]) / 8
            current_bitrate_index += 1
        
        send_frame_time = frame_size / transmitted_bytes_per_ms
        current_delay = send_frame_time + accumulated_time
        accumulated_time = max(0, current_delay - one_frame_interval)
        # print(f'Frame {i}: {frame_size} bytes, send_frame_time: {send_frame_time}, delay: {current_delay}, accumulated_time: {accumulated_time}')
        delay.append(current_delay)
    
    return delay

def get_tail_result(data, ratio):
    data.sort()
    data_len = len(data)
    tail_data = data[int(data_len * ratio):]
    mean_tail_data = np.mean(tail_data)
    return mean_tail_data

def SummarizeCurrentDelay(result_dir, delay, f_parameter_result_file, output_prefix):
    delay = np.array(delay)
    avg_delay = np.mean(delay)
    tail_delay = get_tail_result(delay, 0.9)
    
    vmaf = []
    vmaf_file = f'{result_dir}vmaf_score.log'
    read_data_from_file(vmaf_file, 2, [[], vmaf], ',')
    vmaf = [float(x) for x in vmaf]
    vmaf = np.array(vmaf)
    avg_vmaf = np.mean(vmaf)
    
    f_parameter_result_file.write(f'{output_prefix},{avg_delay},{tail_delay},{avg_vmaf}\n')

def GenerateDelayAndOutputSummary(result_dir, bitrate_indexes, network_bandwidths, response_time, output_prefix):
    delay = CalculateDelay(result_dir, bitrate_indexes, network_bandwidths, response_time)
    write_data_to_file([range(1, len(delay) + 1), delay], f'{result_dir}delay_{response_time}.log')
    SummarizeCurrentDelay(result_dir, delay, f_parameter_result_file, output_prefix)

def GenerateDelay(data, bitrates, bitrate_category_lists, response_times, f_parameter_result_file):
    for bitrate in bitrates:
        bitrate_file = f'input/bitrate_config/{bitrate}'
        bitrate_indexes = []
        network_bandwidths = []
        read_data_from_file(bitrate_file, 2, [bitrate_indexes, network_bandwidths], ',')
        if len(bitrate_indexes) < 2 or len(network_bandwidths) < 2:
            print(f'Error: {bitrate_file} is not valid')
            continue
        for bitrate_category in bitrate_category_lists:
            for response_time in response_times:
                result_dir = f'result/{data}/{bitrate}/{bitrate_category}_0/'
                output_prefix = f'{data},{bitrate},{bitrate_category},{response_time}'
                print(result_dir)
                GenerateDelayAndOutputSummary(result_dir, bitrate_indexes, network_bandwidths, response_time, output_prefix)
                
                result_dir = f'result/{data}/{bitrate}/{bitrate_category}_adaptive_0/'
                output_prefix = f'{data},{bitrate},{bitrate_category}_adaptive,{response_time}'
                GenerateDelayAndOutputSummary(result_dir, bitrate_indexes, network_bandwidths, response_time, output_prefix)


def DrawAdaptiveDelay(data, bitrates, bitrate_category_lists, response_times, parameter_result_file, prefix):
    overall_bitrate = []
    overall_strategy = []
    overall_response_time = []
    overall_delay = []
    overall_vmaf = []
    overall_tail_delay = []
    read_data_from_file(parameter_result_file, 7, [[], overall_bitrate, overall_strategy, overall_response_time, overall_delay, overall_tail_delay, overall_vmaf], ',')

    cmap = plt.get_cmap('Blues')
    colors = [cmap(i) for i in np.linspace(0, 1, len(response_times) + 1)]
    cmap_adaptive = plt.get_cmap('Greens')
    colors_adaptive = [cmap_adaptive(i) for i in np.linspace(0, 1, len(response_times) + 1)]

    for bitrate in bitrates:
        fig, ax = plt.subplots(figsize=(10, 8))
        max_delay = 0
        for response_time in response_times:
            delay = []
            vmaf = []
            strategy = []
            adaptive_delay = []
            adaptive_vmaf = []
            adaptive_strategy = []
            for i in range(len(overall_bitrate)):
                if overall_bitrate[i] == bitrate and int(overall_response_time[i]) == response_time:
                    if ('adaptive' in overall_strategy[i] and float(overall_strategy[i].split('_')[0]) < 0.1) or \
                        ('adaptive' not in overall_strategy[i] and float(overall_strategy[i]) < 0.1):
                        continue
                    if 'adaptive' in overall_strategy[i]:
                        adaptive_delay.append(float(overall_tail_delay[i]))
                        adaptive_vmaf.append(float(overall_vmaf[i]))
                        adaptive_strategy.append(overall_strategy[i].split('_')[0])
                    else:
                        delay.append(float(overall_tail_delay[i]))
                        vmaf.append(float(overall_vmaf[i]))
                        strategy.append(overall_strategy[i])
                    if float(overall_tail_delay[i]) > max_delay:
                        max_delay = float(overall_tail_delay[i])
            print(delay)
            print(vmaf)
            ax.plot(delay, vmaf, label = f'response_frame_count_{response_time}', marker='o', color=colors[int(response_time) + 1])
            ax.plot(adaptive_delay, adaptive_vmaf, label = f'response_frame_count_{response_time}_adaptive', marker='x', color=colors_adaptive[int(response_time) + 1])
            if response_time == 4:
                for i in range(len(delay)):
                    ax.annotate(f'{strategy[i]}', (delay[i], vmaf[i]), textcoords="offset points", xytext=(0,10), ha='center')
                for i in range(len(adaptive_delay)):
                    ax.annotate(f'{adaptive_strategy[i]}', (adaptive_delay[i], adaptive_vmaf[i]), textcoords="offset points", xytext=(0,10), ha='center')
        ax.set_xlabel('Delay (ms)')
        ax.set_ylabel('VMAF')
        ax.legend()
        ax.grid(True, which='both', linestyle='-', alpha=0.3)
        ax.minorticks_on()
        ax.grid(True, which='minor', linestyle='--', alpha=0.1)

        ax.set_xticks(np.arange(0, max_delay, 100))
        plt.tight_layout()
        plt.savefig(f'{prefix}{bitrate}.png')
        plt.clf()
        # exit(0)

if __name__ == "__main__":
    data = 'Lecture_1080p'
    bitrates = ['2to1', '5to1', '5to2', '10to1', '10to2', '10to5', '20to2']
    bitrate_category_lists = ['0.04', '0.05', '0.06', '0.07', '0.08', '0.09', '0.1', '0.2', '0.5', '0.7', '1.0']
    response_times = [0, 1, 2, 3, 4] # frame number
    bitrates = ['10to1']
    bitrate_category_lists = ['0.04', '0.05', '0.06', '0.07', '0.08', '0.09', '0.1', '0.2', '0.3', '0.5', '0.7', '1.0']
    
    parameter_result_file = 'parameter_result_response_time.csv'

    # f_parameter_result_file = open(parameter_result_file, 'w')
    # GenerateDelay(data, bitrates, bitrate_category_lists, response_times, f_parameter_result_file)
    # f_parameter_result_file.close()
    
    prefix = 'scatter/average/tail_delay/vmaf_adaptive/'
    os.system("mkdir -p " + prefix)
    DrawAdaptiveDelay(data, bitrates, bitrate_category_lists, response_times, parameter_result_file, prefix)