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

def filter_data(start_index, end_index, bitrate, strategy, bitrate_filename, strategy_requirement, add_prefix = False):
    filter_condition = str(strategy_requirement)
    # if add_prefix:
    #     filter_condition = '_' + filter_condition + '_'
    print(filter_condition)
    matched_indexes = []
    for i in range(start_index, end_index):
        if bitrate[i] == bitrate_filename and (filter_condition in strategy[i]):
            if not 'adaptive' in filter_condition and 'adaptive' in strategy[i]:
                continue
            matched_indexes.append(i)
    return matched_indexes

def remove_outliers(x, start_index, end_index, threshold):
    outliers_index = []
    for i in range(start_index, end_index):
        if x[i] > threshold:
            outliers_index.append(i)
    return outliers_index

def extract_expected_data(data, indexes):
    expected_data = []
    for i in indexes:
        expected_data.append(data[i])
    return expected_data

def draw_scatter_plot(x, y, x_label, y_label, bitrate, strategy, bitrate_filename, save_fig_name, catergory_filter_list = [], draw_best = False, enable_remove_outliers = False, outlier_thredshold = 0):
    plt.figure(figsize=(5,4))
    scatter_point_size = 30
    # first filter data
    x264_indexes = filter_data(0, len(bitrate), bitrate, strategy, bitrate_filename, '')
    print(bitrate_filename)

    if len(catergory_filter_list) == 0:
        # draw general x264 scatter
        plt.scatter(extract_expected_data(x, x264_indexes),\
                    extract_expected_data(y, x264_indexes),\
                    label='x264', color='blue')
    else:
        n_colors = len(catergory_filter_list)
        colors = cm.rainbow(np.linspace(0, 1, n_colors))
        for i in range(len(catergory_filter_list)):
            add_prefix = True
            if catergory_filter_list[i] == 'adaptive':
                add_prefix = False
            catergory_indexes = filter_data(0, len(bitrate),\
                                            bitrate, strategy,\
                                            bitrate_filename,\
                                            catergory_filter_list[i], add_prefix)
            print(catergory_filter_list[i])
            print(catergory_filter_list[i], catergory_indexes[0], catergory_indexes[-1])
            color = colors[i]
            if i % 2 == 0:
                current_marker = 'o'
            else:
                current_marker = 'x'
            # current_marker = 'o'
            # color = 'blue'
            # if 'adaptive' in catergory_filter_list[i]:
            #     # current_marker = 'x'
            #     color = 'red'
            # if catergory_filter_list[i] == '0.4':
            #     current_marker = 'v'
            #     color = 'black'
            # if catergory_filter_list[i] == 'adaptive':
            #     current_marker = '*'
            #     color = 'red'
            #     scatter_point_size = 100
            # Add labels to each point
            # plt.annotate(f'({catergory_filter_list[i]} : {round(extract_expected_data(x, catergory_indexes)[0], 2)})', (extract_expected_data(x, catergory_indexes)[0], extract_expected_data(y, catergory_indexes)[0]), textcoords="offset points", xytext=(10,0), ha='left', va='center')
            plt.annotate(f'{catergory_filter_list[i]}', (extract_expected_data(x, catergory_indexes)[0], extract_expected_data(y, catergory_indexes)[0]), textcoords="offset points", xytext=(10,0), ha='left', va='center')

            plt.scatter(extract_expected_data(x, catergory_indexes),\
                        extract_expected_data(y, catergory_indexes),\
                        label=catergory_filter_list[i], color=color,\
                        marker=current_marker, s=scatter_point_size)
        if draw_best:
            delay = extract_expected_data(x, x264_indexes)
            psnr = extract_expected_data(y, x264_indexes)
            min_distance = 10000
            min_index = -1
            delay = np.array(delay)
            psnr = np.array(psnr)
            normalized_psnr = (psnr - np.min(psnr)) / (np.max(psnr) - np.min(psnr))
            normalized_delay = (delay - np.min(delay)) / (np.max(delay) - np.min(delay))
            for i in range(0, len(psnr)):
                normalized_distance = np.sqrt((normalized_psnr[i] - 1) ** 2 + normalized_delay[i] ** 2)
                if normalized_distance < min_distance:
                    min_distance = normalized_distance
                    min_index = i
            plt.scatter(extract_expected_data(x, [x264_indexes[min_index]]),\
                        extract_expected_data(y, [x264_indexes[min_index]]),\
                        label='best', color='red', marker='$b$', s=100, alpha=0.5)

    # Add title and labels
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    # plt.title('PSNR consider drop vs Delay for ' + bitrate_filename + '\n (codec setting : tail90 delay)')#, pad=20)

    plt.legend()
    plt.grid()
    plt.tight_layout()

    # Show the plot
    print(save_fig_name)
    plt.savefig(save_fig_name)
    plt.clf()

def draw_scatters(delay, tail_delay, vmaf, bitrate, strategy, bitrate_filename, catergory_filter_list, save_fig_prefix, catergory, file_suffix, draw_best = False):
    output_filename_suffix = bitrate_filename
    if file_suffix != '':
        output_filename_suffix = bitrate_filename + '_' + file_suffix
    draw_scatter_plot(tail_delay, vmaf, 'tail_delay', 'vmaf', bitrate, strategy, bitrate_filename,\
                      save_fig_prefix + 'tail_delay/vmaf/' + output_filename_suffix + '.png',\
                      catergory_filter_list, draw_best)
    draw_scatter_plot(delay, vmaf, 'delay', 'vmaf', bitrate, strategy, bitrate_filename,\
                      save_fig_prefix + 'delay/vmaf/' + output_filename_suffix + '.png',\
                      catergory_filter_list, draw_best)

def draw_average_result_scatter(bitrate_filename, catergory_filter_list, file_suffix):
    data_file = 'parameter_result' + file_suffix + '.csv'
    print(data_file)
    save_fig_prefix = 'scatter/average/'
    bitrate = []
    strategy = []
    delay = []
    tail_delay = []
    vmaf = []

    read_data_from_file(data_file, 6, [[], bitrate, strategy, delay, tail_delay, vmaf], ',')
    delay = [float(i) for i in delay]
    tail_delay = [float(i) for i in tail_delay]
    vmaf = [float(i) for i in vmaf]

    draw_scatters(delay, tail_delay, vmaf, bitrate, strategy, bitrate_filename, catergory_filter_list, save_fig_prefix, '', file_suffix, False)

def draw_every_trail_scatter(bitrate_filename, catergory_filter_list, file_suffix):
    data_file = 'every_trail.csv'
    save_fig_prefix = 'scatter/every_trail/'
    bitrate = []
    strategy = []
    delay = []
    tail_delay = []
    vmaf = []

    read_data_from_file(data_file, 7, [[], bitrate, strategy, [], delay, tail_delay, vmaf], ',')
    # print(bitrate)
    delay = [float(i) for i in delay]
    tail_delay = [float(i) for i in tail_delay]
    vmaf = [float(i) for i in vmaf]

    draw_scatters(delay, tail_delay, vmaf, bitrate, strategy, bitrate_filename, catergory_filter_list, save_fig_prefix, '',  file_suffix)

if __name__ == "__main__":
    os.system("mkdir -p " + 'scatter/average/delay/vmaf')
    os.system("mkdir -p " + 'scatter/every_trail/delay/vmaf')
    # os.system("mkdir -p " + 'scatter/average/tail_delay/vmaf')
    # os.system("mkdir -p " + 'scatter/every_trail/tail_delay/vmaf')

    bitrates = ['static_20mbps', 'static_10mbps', 'static_5mbps', 'static_2mbps', 'static_1mbps', '2to1', '5to1', '5to2', '10to1', '10to2', '10to5', '20to2', 'static_500kbps']
    # bitrates = ['10to1']
    bitrate_category_list = ['0.03', '0.04', '0.05', '0.06', '0.07', '0.08', '0.09', '0.1', '0.2', '0.5', '0.7', '1.0']
    # bitrate_category_list = ['0.04', '0.05', '0.06', '0.07', '0.08', '0.09', '0.1', '0.2', '0.5', '0.7',
    #                          '0.04_adaptive', '0.05_adaptive', '0.06_adaptive', '0.07_adaptive', '0.08_adaptive', '0.09_adaptive', '0.1_adaptive', '0.2_adaptive', '0.5_adaptive', '0.7_adaptive']

    for bitrate in bitrates:
        draw_average_result_scatter(bitrate, bitrate_category_list, '')
        # draw_every_trail_scatter(bitrate, bitrate_category_list, '')