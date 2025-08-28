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

def filter_data(start_index, end_index, bitrate, bitrate_filename, strategy, strategy_requirement, datas, data, add_prefix = False):
    filter_condition = str(strategy_requirement)
    if add_prefix:
        filter_condition = '_' + filter_condition + '_'
    print(filter_condition)
    matched_indexes = []
    for i in range(start_index, end_index):
        if bitrate[i] == bitrate_filename and (filter_condition in strategy[i]) and (datas[i] == data):
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

def draw_scatter_plot(x, y, x_label, y_label, bitrate, strategy, datas, bitrate_filename, data, save_fig_name, catergory_filter_list = [], draw_best = False, enable_remove_outliers = False, outlier_thredshold = 0):
    plt.figure(figsize=(5,4))
    plt.rcParams['font.size'] = 14
    scatter_point_size = 50
    # first filter data
    x264_indexes = filter_data(0, len(bitrate), bitrate, bitrate_filename, strategy, '', datas, data)
    print(bitrate_filename)

    n_colors = len(catergory_filter_list)
    colors = cm.rainbow(np.linspace(0, 1, n_colors))
    for i in range(len(catergory_filter_list)):
        catergory_indexes = filter_data(0, len(bitrate),\
                                        bitrate, bitrate_filename,\
                                        strategy, catergory_filter_list[i],\
                                        datas, data)
        print(catergory_filter_list[i], data, bitrate_filename)
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
        if 'adaptive' in catergory_filter_list[i]:
            current_marker = '*'
            color = 'red'
            scatter_point_size = 100
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

    # plt.legend()
    plt.grid()
    plt.tight_layout()

    # Show the plot
    print(save_fig_name)
    plt.savefig(save_fig_name)
    plt.clf()

def draw_average_result_scatter(bitrate_filename, catergory_filter_list, data):
    data_file = 'every_trail.csv'
    print(data_file)
    save_fig_prefix = 'scatter/'
    datas = []
    bitrate = []
    strategy = []
    delay = []
    tail_delay = []
    vmaf = []
    psnr = []

    read_data_from_file(data_file, 7, [datas, bitrate, strategy, delay, tail_delay, vmaf, psnr], ',')
    delay = [float(i) for i in delay]
    tail_delay = [float(i) for i in tail_delay]
    vmaf = [float(i) for i in vmaf]
    psnr = [float(i) for i in psnr]

    # draw_scatter_plot(tail_delay, psnr, 'tail delay', 'psnr', bitrate, strategy, datas, bitrate_filename, data,\
    #                   save_fig_prefix + f'psnr_tail_delay/{data}_{bitrate_filename}.png',\
    #                   catergory_filter_list, False)
    # draw_scatter_plot(delay, psnr, 'delay', 'psnr', bitrate, strategy, datas, bitrate_filename, data,\
    #                   save_fig_prefix + f'psnr_delay/{data}_{bitrate_filename}.png',\
    #                   catergory_filter_list, True)
    draw_scatter_plot(tail_delay, vmaf, 'tail delay', 'vmaf', bitrate, strategy, datas, bitrate_filename, data,\
                      save_fig_prefix + f'vmaf_tail_delay_part/{data}_{bitrate_filename}.png',\
                      catergory_filter_list, False)
    draw_scatter_plot(delay, vmaf, 'delay', 'vmaf', bitrate, strategy, datas, bitrate_filename, data,\
                      save_fig_prefix + f'vmaf_delay_part/{data}_{bitrate_filename}.png',\
                      catergory_filter_list, False)

if __name__ == "__main__":
    # os.system("mkdir -p " + 'scatter/psnr_delay/')
    # os.system("mkdir -p " + 'scatter/psnr_tail_delay/')
    os.system("mkdir -p " + 'scatter/vmaf_delay_part/')
    os.system("mkdir -p " + 'scatter/vmaf_tail_delay_part/')
    datas = ['Game_gray', 'Lecture1080p']#, 'Game_minecraft', 'Game_scene_change', 'Game_screen', 'Game_shoot', 'Game_shoot_static', 'ReadySteadyGo', 'static']
    bitrates = ['static_10mbps', 'static_5mbps', 'static_2mbps', 'static_1mbps']
    datas = ['Game_gray_part', 'Lecture1080p', 'scene_change']#, 'ReadySteadyGo']
    # datas = ['ReadySteadyGo']
    # speeds = [1, 2, 4, 8]
    speeds = [1]
    bitrates = ['10to1', '5to1', '2to1', '10to5', '10to2']
    # bitrates = ['static_5mbps']
    bitrate_category_list = ['0.04', '0.06', '0.08', '0.1', '0.3', '0.5', '0.7', '1.0']#, 'adaptive']#, 'adaptive2']
    bitrate_category_list = ['0.3', '0.3_0.04_10', '0.3_0.06_10', '0.3_0.08_10', '0.3_0.1_10', '0.3_0.2_10']#, 'adaptive2']
    # bitrate_category_list = ['0.04', '0.05', '0.06', '0.07', '0.08', '0.09', '0.1', '0.2', '0.5', '0.7',
    #                          '0.04_adaptive', '0.05_adaptive', '0.06_adaptive', '0.07_adaptive', '0.08_adaptive', '0.09_adaptive', '0.1_adaptive', '0.2_adaptive', '0.5_adaptive', '0.7_adaptive']

    bitrate_category_list = [x + '_part' for x in bitrate_category_list]
    print(bitrate_category_list)
    # exit(0)
        
    for data in datas:
        for speed in speeds:
            data_file = data
            if speed != 1:
                data_file = f'{data}_{speed}x'
            print(f'Processing data: {data_file}')
            for bitrate in bitrates:
                draw_average_result_scatter(bitrate, bitrate_category_list, data_file)
                # exit(0)
            # exit(0)