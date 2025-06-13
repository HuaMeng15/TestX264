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

def get_tail_result(data, ratio):
    data.sort()
    data_len = len(data)
    tail_data = data[int(data_len * ratio):]
    mean_tail_data = np.mean(tail_data)
    return mean_tail_data

def DrawAdaptiveDelay(data, bitrates, bitrate_category_lists, response_times, result_file):
    overall_bitrate = []
    overall_strategy = []
    overall_response_time = []
    overall_delay = []
    overall_vmaf = []
    overall_tail_delay = []
    read_data_from_file(result_file, 7, [[], overall_bitrate, overall_strategy, overall_response_time, overall_delay, overall_tail_delay, overall_vmaf], ',')

    cmap = plt.get_cmap('Blues')
    colors = [cmap(i) for i in np.linspace(0, 1, len(response_times) + 1)]
    cmap_adaptive = plt.get_cmap('Greens')
    colors_adaptive = [cmap_adaptive(i) for i in np.linspace(0, 1, len(response_times) + 1)]

    for bitrate in bitrates:
        fig, ax = plt.subplots(figsize=(5,4))
        plt.xticks(fontsize=18)#, weight='bold')
        plt.yticks(fontsize=18)#, weight='bold')
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
                        strategy.append(overall_strategy[i].split('_')[0])
                    if float(overall_tail_delay[i]) > max_delay:
                        max_delay = float(overall_tail_delay[i])
            print(delay)
            print(vmaf)
            # ax.plot(delay, vmaf, label = f'response_frame_count_{response_time}', marker='o', color=colors[int(response_time) + 1])
            # ax.plot(adaptive_delay, adaptive_vmaf, label = f'response_frame_count_{response_time}_adaptive', marker='x', color=colors_adaptive[int(response_time) + 1])
            ax.plot(delay, vmaf, label = f'consistent', marker='o', color='blue', linewidth=2.5)
            ax.plot(adaptive_delay, adaptive_vmaf, label = f'  adaptive\n (our design)', marker='o', color='green', linewidth=2.5)
            # if response_time == 3:
            for i in range(len(delay)):
                if strategy[i] == '1.0' or strategy[i] == '0.7':
                    ax.annotate(f'{strategy[i]}x', (delay[i], vmaf[i]), textcoords="offset points", xytext=(0,-25), ha='center', fontsize=18)
                else:
                    ax.annotate(f'{strategy[i]}x', (delay[i], vmaf[i]), textcoords="offset points", xytext=(20,-15), ha='center', fontsize=18)
            for i in range(len(adaptive_delay)):
                if strategy[i] == '1.0':
                    ax.annotate(f'{adaptive_strategy[i]}x', (adaptive_delay[i], adaptive_vmaf[i]), textcoords="offset points", xytext=(20,-15), ha='center', fontsize=18)
                else:
                    ax.annotate(f'{adaptive_strategy[i]}x', (adaptive_delay[i], adaptive_vmaf[i]), textcoords="offset points", xytext=(24,-5), ha='center', fontsize=18)
        ax.set_xlabel('Delay (ms)', fontsize=20)
        ax.set_ylabel('VMAF', fontsize=20)
        ax.legend(fontsize=18, loc='best')
        ax.grid(True, which='both', linestyle='-', alpha=0.7)
        ax.minorticks_on()
        ax.grid(True, which='minor', linestyle='--', alpha=0.3)

        ax.set_xticks(np.arange(600, max_delay, 200))
        plt.tight_layout()
        plt.savefig(f'adpative_vbv_buffer_size.png')
        plt.clf()
        # exit(0)

def DrawResponseTime(data, bitrates, bitrate_category_lists, response_times, result_file):
    overall_bitrate = []
    overall_strategy = []
    overall_response_time = []
    overall_delay = []
    overall_vmaf = []
    overall_tail_delay = []
    read_data_from_file(result_file, 7, [[], overall_bitrate, overall_strategy, overall_response_time, overall_delay, overall_tail_delay, overall_vmaf], ',')

    cmap = plt.get_cmap('Blues')
    colors = [cmap(i) for i in np.linspace(0, 1, len(response_times) + 1)]
    cmap_adaptive = plt.get_cmap('Greens')
    colors_adaptive = [cmap_adaptive(i) for i in np.linspace(0, 1, len(response_times) + 2)]

    for bitrate in bitrates:
        fig, ax = plt.subplots(figsize=(5,4))
        plt.xticks(fontsize=18)#, weight='bold')
        plt.yticks(fontsize=18)#, weight='bold')
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
                        strategy.append(overall_strategy[i].split('_')[0])
                    if float(overall_tail_delay[i]) > max_delay:
                        max_delay = float(overall_tail_delay[i])
            print(delay)
            print(vmaf)
            # ax.plot(delay, vmaf, label = f'response_frame_count_{response_time}', marker='o', color=colors[int(response_time) + 1])
            # ax.plot(adaptive_delay, adaptive_vmaf, label = f'response_frame_count_{response_time}_adaptive', marker='x', color=colors_adaptive[int(response_time) + 1])
            ax.plot(adaptive_delay, adaptive_vmaf, label = f'response time: {response_time}', marker='o', color=colors_adaptive[int(response_time) + 1], linewidth=2.5)
            if response_time == 4:
                ax.plot(delay, vmaf, label = f'consistent', marker='o', color='blue', linewidth=2.5)
            # ax.plot(adaptive_delay, adaptive_vmaf, label = f'  adaptive\n (our design)', marker='o', color='green', linewidth=2.5)
            if response_time == 4:
                for i in range(len(delay)):
                    if strategy[i] == '1.0' or strategy[i] == '0.7' or strategy[i] == '0.5':
                        ax.annotate(f'{strategy[i]}x', (delay[i], vmaf[i]), textcoords="offset points", xytext=(0,-25), ha='center', fontsize=14)
                    else:
                        ax.annotate(f'{strategy[i]}x', (delay[i], vmaf[i]), textcoords="offset points", xytext=(20,-15), ha='center', fontsize=14)
            if response_time == 2:
                for i in range(len(adaptive_delay)):
                    if strategy[i] == '1.0':
                        ax.annotate(f'{adaptive_strategy[i]}x', (adaptive_delay[i], adaptive_vmaf[i]), textcoords="offset points", xytext=(20,-15), ha='center', fontsize=14)
                    else:
                        ax.annotate(f'{adaptive_strategy[i]}x', (adaptive_delay[i], adaptive_vmaf[i]), textcoords="offset points", xytext=(24,-5), ha='center', fontsize=14)
        ax.set_xlabel('Delay (ms)', fontsize=20)
        ax.set_ylabel('VMAF', fontsize=20)
        ax.legend(fontsize=10, loc='best')
        ax.grid(True, which='both', linestyle='-', alpha=0.7)
        ax.minorticks_on()
        ax.grid(True, which='minor', linestyle='--', alpha=0.3)

        ax.set_xticks(np.arange(100, max_delay, 300))
        plt.tight_layout()
        plt.savefig(f'response_time.png')
        plt.clf()
        # exit(0)

if __name__ == "__main__":
    data = 'Lecture_1080p'
    bitrates = ['10to1']
    bitrate_category_lists = ['0.1', '0.3', '0.5', '0.7', '1.0']
    response_times = [1, 2, 3, 4] # frame number
    # response_times = [3] # frame number
    
    result_file = 'every_trail.csv'

    # DrawAdaptiveDelay(data, bitrates, bitrate_category_lists, response_times, result_file)
    DrawResponseTime(data, bitrates, bitrate_category_lists, response_times, result_file)