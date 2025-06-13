import re
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


def ExtractNormalizedVmaf(data, bitrates, bitrate_category_list, output_file):
    overall_bitrate = []
    overall_strategy = []
    overall_avg_delay = []
    overall_tail_delay = []
    overall_vmaf = []
    parameter_result_file = 'parameter_result.csv'
    read_data_from_file(parameter_result_file, 6, [[], overall_bitrate, overall_strategy, overall_avg_delay, overall_tail_delay, overall_vmaf], ',')

    f_output_file = open(output_file, 'w')
    
    for bitrate_file in bitrates:
        vmaf = []
        start_index = -1
        for i in range(len(overall_bitrate)):
            if overall_bitrate[i] == bitrate_file and '0.03' not in overall_strategy[i]:
                if start_index == -1:
                    start_index = i
                vmaf.append(float(overall_vmaf[i]))

        vmaf = np.array(vmaf)
        vmaf = (vmaf - np.min(vmaf)) / (np.max(vmaf) - np.min(vmaf))
        
        print(vmaf)
        
        for i in range(len(vmaf)):
            index = start_index + i
            f_output_file.write(f'{data},{bitrate_file},{overall_strategy[index]},{overall_avg_delay[index]},{overall_tail_delay[index]},{overall_vmaf[index]},{vmaf[i]}\n')
    f_output_file.close()

def DrawNormalizedVmaf(bitrates, bitrate_category_list, output_file, delay_threshold):
    overall_bitrates = []
    overall_strategy = []
    overall_avg_delay = []
    overall_tail_delay = []
    overall_vmaf = []
    read_data_from_file(output_file, 7, [[], overall_bitrates, overall_strategy, overall_avg_delay, overall_tail_delay, [], overall_vmaf], ',')
    overall_vmaf = [float(x) for x in overall_vmaf]
    overall_tail_delay = [float(x) for x in overall_tail_delay]

    plt.figure(figsize=(10,8))

    n_colors = len(bitrate_category_list)
    colors = cm.rainbow(np.linspace(0, 1, n_colors))
    
    for index in range(len(bitrate_category_list)):
        strategy = bitrate_category_list[index]
        bitrate = []
        vmaf = []
        for i in range(len(overall_strategy)):
            if strategy in overall_strategy[i]:
                bitrate_number = int(re.findall(r'\d+', overall_bitrates[i])[0])
                if bitrate_number > 100:
                    bitrate_number = bitrate_number / 1000
                bitrate.append(bitrate_number)
                vmaf.append(round(overall_vmaf[i], 4))
                print(strategy, bitrate_number, overall_vmaf[i])
        current_marker = 'o'
        if index % 2 == 0:
            current_marker = 'x'
        plt.plot(bitrate, vmaf, label=strategy, marker=current_marker, color=colors[index])

    best_vmaf = []
    best_bitrate = []
    best_strategy = []

    for bitrate in bitrates:
        current_best_vmaf = 0
        current_best_bitrate = 0
        current_best_strategy = ''
        for i in range(len(overall_bitrates)):
            if bitrate in overall_bitrates[i]:
                bitrate_number = int(re.findall(r'\d+', overall_bitrates[i])[0])
                if bitrate_number > 100:
                    bitrate_number = bitrate_number / 1000
                if overall_tail_delay[i] < delay_threshold and overall_vmaf[i] > current_best_vmaf:
                    current_best_vmaf = overall_vmaf[i]
                    current_best_bitrate = bitrate_number
                    current_best_strategy = overall_strategy[i].split('_')[0]
        if current_best_vmaf > 0:
            best_vmaf.append(current_best_vmaf)
            best_bitrate.append(current_best_bitrate)
            best_strategy.append(current_best_strategy)
    
    print('Best VMAF:', best_vmaf)
    print('Best Bitrate:', best_bitrate)
    print('Best Strategy:', best_strategy)
    plt.plot(best_bitrate, best_vmaf, label='Best VMAF', marker='*', color='black', markersize=10)
    
    for i in range(len(best_bitrate)):
        plt.annotate(f'({best_bitrate[i]}mbps,{best_strategy[i]})', (best_bitrate[i], best_vmaf[i]), textcoords="offset points", xytext=(0, 10), ha='center')
    
    plt.xlabel('Different Bitrates (mbps)')
    plt.ylabel('Normalized VMAF')
    plt.title('Normalized VMAF in Different Bitrates')
    plt.legend()
    plt.grid()
    plt.savefig(f'normalized_vmaf_delay_threshold_{delay_threshold}.png')

if __name__ == "__main__":
    data = 'Lecture_1080p'
    # bitrates = ['static_20mbps', 'static_10mbps', 'static_5mbps', 'static_2mbps', 'static_1mbps', 'static_500kbps']
    bitrates = ['static_20mbps', 'static_10mbps', 'static_5mbps', 'static_2mbps', 'static_1mbps', 'static_500kbps']
    bitrate_category_list = ['0.04', '0.05', '0.06', '0.07', '0.08', '0.09', '0.1', '0.2', '0.5', '0.7', '1.0']
    
    delay_thresholds = [30, 40, 50, 60]
    
    for delay_threshold in delay_thresholds:
        output_file = 'parameter_normalized_result.csv'
        ExtractNormalizedVmaf(data, bitrates, bitrate_category_list, output_file)
        DrawNormalizedVmaf(bitrates, bitrate_category_list, output_file, delay_threshold)