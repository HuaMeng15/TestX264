import os
import csv
import numpy as np

def output_parameter_result(data, bitrate, strategy, delay, tail_delay, vmaf):
    delay = np.array(delay)
    tail_delay = np.array(tail_delay)
    vmaf = np.array(vmaf)
    
    parameter_result_file = 'parameter_result.csv'
    with open(parameter_result_file, 'a') as f:
        f.write(f'{data},{bitrate},{strategy},{np.mean(delay)},{np.mean(tail_delay)},{np.mean(vmaf)}\n')

def generate_parameter_results():
    data = 'Lecture_1080p'
    bitrate = ''
    strategy = ''
    delay = []
    tail_delay = []
    vmaf = []

    every_trail_file = 'every_trail.csv'

    lines = open(every_trail_file,'r').read().split('\n')
    for line in lines:
        line_list = line.split(',')
        if len(line_list) < 7 or line_list[0] != data:
            continue
        items = line_list[2].split('_')
        current_strategy = line_list[2]
        if (len(items) > 2):
            current_strategy = items[0] + '_' + items[1]
        print(current_strategy)
        if bitrate == '':
            bitrate = line_list[1]
            strategy = current_strategy
        if bitrate != line_list[1] or strategy != current_strategy:
            output_parameter_result(data, bitrate, strategy, delay, tail_delay, vmaf)
            bitrate = line_list[1]
            strategy = current_strategy
            delay = []
            tail_delay = []
            vmaf = []

        delay.append(float(line_list[4]))
        tail_delay.append(float(line_list[5]))
        vmaf.append(float(line_list[6]))
    output_parameter_result(data, bitrate, strategy, delay, tail_delay, vmaf)

if __name__ == "__main__":
    generate_parameter_results()