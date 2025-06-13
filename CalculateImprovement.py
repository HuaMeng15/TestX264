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

def CalcAdaptiveImprove(data, bitrates, bitrate_category_lists, response_times, result_file):
    overall_bitrate = []
    overall_strategy = []
    overall_response_time = []
    overall_delay = []
    overall_vmaf = []
    overall_tail_delay = []
    read_data_from_file(result_file, 7, [[], overall_bitrate, overall_strategy, overall_response_time, overall_delay, overall_tail_delay, overall_vmaf], ',')
    
    output_file = f'improvement.csv'
    f_output_file = open(output_file, 'w')
    
    delay_min = 100
    delay_max = 0
    vmaf_min = 100
    vmaf_max = 0

    for bitrate in bitrates:
        for strategy in bitrate_category_lists:
            for response_time in response_times:
                original_tail_delay = 0
                original_vmaf = 0
                adaptive_tail_delay = 0
                adaptive_vmaf = 0
                for i in range(len(overall_bitrate)):
                    if overall_bitrate[i] == bitrate and int(overall_response_time[i]) == response_time:
                        if strategy in overall_strategy[i]:
                            if 'adaptive' in overall_strategy[i]:
                                adaptive_tail_delay = float(overall_tail_delay[i])
                                adaptive_vmaf = float(overall_vmaf[i])
                            else:
                                original_tail_delay = float(overall_tail_delay[i])
                                original_vmaf = float(overall_vmaf[i])
                delay_improvement = (original_tail_delay - adaptive_tail_delay) / original_tail_delay
                vmaf_improvement = (original_vmaf - adaptive_vmaf) / original_vmaf
                if delay_improvement < delay_min:
                    delay_min = delay_improvement
                if delay_improvement > delay_max:
                    delay_max = delay_improvement
                if vmaf_improvement < vmaf_min:
                    vmaf_min = vmaf_improvement
                if vmaf_improvement > vmaf_max:
                    vmaf_max = vmaf_improvement
                f_output_file.write(f'{bitrate},{strategy},{response_time},{original_tail_delay},{adaptive_tail_delay},{original_vmaf},{adaptive_vmaf},{original_tail_delay - adaptive_tail_delay},{adaptive_vmaf - original_vmaf}, {delay_improvement},{vmaf_improvement}\n')
    f_output_file.write(f'min_delay_improvement: {delay_min}, max_delay_improvement: {delay_max}, min_vmaf_improvement: {vmaf_min}, max_vmaf_improvement: {vmaf_max}\n')
    f_output_file.close()

def CalcResponseTimeImprove(data, bitrates, bitrate_category_lists, response_times, result_file):
    overall_bitrate = []
    overall_strategy = []
    overall_response_time = []
    overall_delay = []
    overall_vmaf = []
    overall_tail_delay = []
    read_data_from_file(result_file, 7, [[], overall_bitrate, overall_strategy, overall_response_time, overall_delay, overall_tail_delay, overall_vmaf], ',')
    
    output_file = f'improvement.csv'
    f_output_file = open(output_file, 'w')
    
    delay_min = 100
    delay_max = 0
    vmaf_min = 100
    vmaf_max = 0

    for bitrate in bitrates:
        for strategy in bitrate_category_lists:
            for i in range(len(response_times) - 1):
                original_response_time = response_times[i + 1]
                predict_response_time = response_times[i]
                original_tail_delay = 0
                original_vmaf = 0
                adaptive_tail_delay = 0
                adaptive_vmaf = 0

                for i in range(len(overall_bitrate)):
                    if overall_bitrate[i] == bitrate and strategy in overall_strategy[i] and 'adaptive' not in overall_strategy[i]:
                        if int(overall_response_time[i]) == original_response_time:
                            original_tail_delay = float(overall_tail_delay[i])
                            original_vmaf = float(overall_vmaf[i])
                        if int(overall_response_time[i]) == predict_response_time:
                            adaptive_tail_delay = float(overall_tail_delay[i])
                            adaptive_vmaf = float(overall_vmaf[i])
                delay_improvement = (original_tail_delay - adaptive_tail_delay) / original_tail_delay
                vmaf_improvement = (original_vmaf - adaptive_vmaf) / original_vmaf
                if delay_improvement < delay_min:
                    delay_min = delay_improvement
                if delay_improvement > delay_max:
                    delay_max = delay_improvement
                if vmaf_improvement < vmaf_min:
                    vmaf_min = vmaf_improvement
                if vmaf_improvement > vmaf_max:
                    vmaf_max = vmaf_improvement
                f_output_file.write(f'{bitrate},{strategy},{original_response_time},{predict_response_time},{original_tail_delay},{adaptive_tail_delay},{original_vmaf},{adaptive_vmaf},{original_tail_delay - adaptive_tail_delay},{adaptive_vmaf - original_vmaf}, {delay_improvement},{vmaf_improvement}\n')
    f_output_file.write(f'min_delay_improvement: {delay_min}, max_delay_improvement: {delay_max}, min_vmaf_improvement: {vmaf_min}, max_vmaf_improvement: {vmaf_max}\n')
    f_output_file.close()

def CalcOverallImprove(data, bitrates, bitrate_category_lists, response_times, result_file):
    overall_bitrate = []
    overall_strategy = []
    overall_response_time = []
    overall_delay = []
    overall_vmaf = []
    overall_tail_delay = []
    read_data_from_file(result_file, 7, [[], overall_bitrate, overall_strategy, overall_response_time, overall_delay, overall_tail_delay, overall_vmaf], ',')
    
    output_file = f'improvement.csv'
    f_output_file = open(output_file, 'w')
    
    delay_min = 100
    delay_max = 0
    vmaf_min = 100
    vmaf_max = 0

    for bitrate in bitrates:
        for strategy in bitrate_category_lists:
            for i in range(len(response_times) - 1):
                original_response_time = response_times[i + 1]
                predict_response_time = response_times[i]
                original_tail_delay = 0
                original_vmaf = 0
                adaptive_tail_delay = 0
                adaptive_vmaf = 0

                for i in range(len(overall_bitrate)):
                    if overall_bitrate[i] == bitrate and strategy in overall_strategy[i]:
                        if int(overall_response_time[i]) == original_response_time and 'adaptive' not in overall_strategy[i]:
                            original_tail_delay = float(overall_tail_delay[i])
                            original_vmaf = float(overall_vmaf[i])
                        if int(overall_response_time[i]) == predict_response_time and 'adaptive' in overall_strategy[i]:
                            adaptive_tail_delay = float(overall_tail_delay[i])
                            adaptive_vmaf = float(overall_vmaf[i])
                delay_improvement = (original_tail_delay - adaptive_tail_delay) / original_tail_delay
                vmaf_improvement = (original_vmaf - adaptive_vmaf) / original_vmaf
                if delay_improvement < delay_min:
                    delay_min = delay_improvement
                if delay_improvement > delay_max:
                    delay_max = delay_improvement
                if vmaf_improvement < vmaf_min:
                    vmaf_min = vmaf_improvement
                if vmaf_improvement > vmaf_max:
                    vmaf_max = vmaf_improvement
                f_output_file.write(f'{bitrate},{strategy},{original_response_time},{predict_response_time},{original_tail_delay},{adaptive_tail_delay},{original_vmaf},{adaptive_vmaf},{original_tail_delay - adaptive_tail_delay},{adaptive_vmaf - original_vmaf}, {delay_improvement},{vmaf_improvement}\n')
    f_output_file.write(f'min_delay_improvement: {delay_min}, max_delay_improvement: {delay_max}, min_vmaf_improvement: {vmaf_min}, max_vmaf_improvement: {vmaf_max}\n')
    f_output_file.close()

if __name__ == "__main__":
    data = 'Lecture_1080p'
    bitrates = ['10to1']
    bitrate_category_lists = ['0.1', '0.3', '0.5', '0.7', '1.0']
    response_times = [1, 2, 3, 4] # frame number
    # response_times = [2] # frame number
    
    result_file = 'every_trail.csv'

    # CalcAdaptiveImprove(data, bitrates, bitrate_category_lists, response_times, result_file)
    # CalcResponseTimeImprove(data, bitrates, bitrate_category_lists, response_times, result_file)
    CalcOverallImprove(data, bitrates, bitrate_category_lists, response_times, result_file)