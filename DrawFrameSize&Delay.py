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

def GenerateBitratePoint(bitrate_indexes, network_bandwidths, frame_count):
    # based on bitrate config, create bitrate point
    current_bitrate_index = 0
    current_bitrate = network_bandwidths[current_bitrate_index]
    bitrates = []
    for i in range(frame_count):
        if current_bitrate_index < len(bitrate_indexes) and i == bitrate_indexes[current_bitrate_index]:
            print(i, current_bitrate_index, current_bitrate)
            current_bitrate = network_bandwidths[current_bitrate_index]
            current_bitrate_index += 1
        bitrates.append(current_bitrate)
    return bitrates
    

def ExtractFrameSize(output_dir):
    send_file = f'{output_dir}send.log'
    frame_sizes = []
    read_data_from_file(send_file, 3, [[], [], frame_sizes], ':')
    frame_sizes = [(int(x) * 8 * 30 / 1000) for x in frame_sizes]
    return frame_sizes

def ExtractDelay(output_dir):
    delay_file = f'{output_dir}delay.log'
    delay = []
    read_data_from_file(delay_file, 2, [[], delay], ',')
    delay = [float(x) for x in delay]
    return delay

def ExtractVmaf(output_dir):
    vmaf_file = f'{output_dir}vmaf_score.log'
    vmaf = []
    read_data_from_file(vmaf_file, 2, [[], vmaf], ',')
    vmaf = [float(x) for x in vmaf]
    return vmaf

def DrawFrameSize(output_dir, bitrate_indexes, network_bandwidths, bitrate_category, start_index=0, end_index=10000):
    frame_sizes = ExtractFrameSize(output_dir)
    frame_index = list(range(len(frame_sizes)))
    
    bitrates = GenerateBitratePoint(bitrate_indexes, network_bandwidths, len(frame_sizes))
    
    plt.figure(figsize=(16,8))
    plt.rcParams['font.size'] = 20
    plt.ylim(0, 6500)
    plt.plot(frame_index[start_index:end_index], frame_sizes[start_index:end_index], label='Frame Size', color='blue', linewidth=2.5)
    plt.plot(frame_index[start_index:end_index], bitrates[start_index:end_index], label='Network Bandwidth', color='red', linewidth=2.5)
    plt.xlabel('Frame Index', fontsize=20)
    plt.ylabel('Frame Size (kbps)', fontsize=20)
    plt.legend()
    plt.grid()
    plt.tight_layout()
    output_file = f'frame_size_20.png'
    plt.savefig(output_file)
    plt.close()

def DrawPlot(data, data_index, x_label, y_label, start_index, end_index, output_file, data_label):
    plt.figure(figsize=(16,8))
    plt.rcParams['font.size'] = 20
    plt.plot(data_index[start_index:end_index], data[start_index:end_index], label=data_label, color='blue', linewidth=2.5)
    plt.xlabel(x_label, fontsize=20)
    plt.ylabel(y_label, fontsize=20)
    plt.legend()
    plt.grid()
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()

def DrawDelay(output_dir, bitrate_indexes, network_bandwidths, bitrate_category, start_index=0, end_index=10000):
    frame_sizes = ExtractDelay(output_dir)
    frame_index = list(range(len(frame_sizes)))
    
    DrawPlot(frame_sizes, frame_index, 'Frame Index', 'Delay (ms)', start_index, end_index, f'{output_dir}delay.png', 'Delay (ms)')

def DrawVmaf(output_dir, bitrate_indexes, network_bandwidths, bitrate_category, start_index=0, end_index=10000):
    vmaf = ExtractVmaf(output_dir)
    frame_index = list(range(len(vmaf)))
    
    DrawPlot(vmaf, frame_index, 'Frame Index', 'VMAF', start_index, end_index, f'{output_dir}vmaf.png', 'VMAF')

def DrawPSNR(output_dir, bitrate_indexes, network_bandwidths, bitrate_category, start_index=0, end_index=10000):
    psnr_file = f'{output_dir}psnr_score.log'
    psnr = []
    read_data_from_file(psnr_file, 2, [[], psnr], ',')
    psnr = [float(x) for x in psnr]
    frame_index = list(range(len(psnr)))
    
    DrawPlot(psnr, frame_index, 'Frame Index', 'PSNR (dB)', start_index, end_index, f'{output_dir}psnr.png', 'PSNR (dB)')


def DrawThreeSubplots(output_dir):
    bitrate_file = f'input/bitrate_config/10to1'
    bitrate_indexes = []
    network_bandwidths = []
    read_data_from_file(bitrate_file, 2, [bitrate_indexes, network_bandwidths], ',')
    bitrate_indexes = [int(x) for x in bitrate_indexes]
    network_bandwidths = [int(x) for x in network_bandwidths]
    
    frame_sizes5 = ExtractFrameSize(f'{output_dir}0.5_0/')
    frame_index = list(range(len(frame_sizes5)))
    delay5 = ExtractDelay(f'{output_dir}0.5_0/')
    
    frame_sizes04 = ExtractFrameSize(f'{output_dir}0.04_0/')
    delay04 = ExtractDelay(f'{output_dir}0.04_0/')

    frame_sizes_adaptive = ExtractFrameSize(f'{output_dir}0.5_adaptive_0/')
    delay_adaptive = ExtractDelay(f'{output_dir}0.5_adaptive_0/')

    bitrates = GenerateBitratePoint(bitrate_indexes, network_bandwidths, len(frame_sizes5))
    
    # Settings
    start_index = 80
    end_index = 130
    fontsize = 18

    fig, axes = plt.subplots(1, 3, figsize=(15,5), sharey=True)
    plt.xticks(fontsize=fontsize)
    plt.yticks(fontsize=fontsize)
    # plt.subplots_adjust(wspace=0.1)

    plt.rcParams.update({'font.size': fontsize})

    for ax in axes:
        ax.tick_params(axis='both', which='major', labelsize=fontsize)

    axes[0].plot(frame_index[start_index:end_index], frame_sizes5[start_index:end_index], 'b', linewidth=2.5)
    axes[0].plot(frame_index[start_index:end_index], bitrates[start_index:end_index], 'black', linewidth=2.5, linestyle='--')
    # axes[0].set_title(f"(a) 0.5x")
    axes[0].set_ylabel("Frame Size (kbps)", fontsize=22)
    # axes[0].set_xlabel("Frame Index", fontsize=fontsize)
    axes[0].grid(True, linestyle='--', alpha=0.7)
    ax0_right = axes[0].twinx()
    ax0_right.plot(frame_index[start_index:end_index], delay5[start_index:end_index], 'r', linewidth=2.5, label='Delay (ms)')
    ax0_right.set_ylim(0, 360)

    axes[1].plot(frame_index[start_index:end_index], frame_sizes04[start_index:end_index], 'b', linewidth=2.5, label='Frame Size (kbps)')
    axes[1].plot(frame_index[start_index:end_index], bitrates[start_index:end_index], 'black', linewidth=2.5, linestyle='--', label='Bandwidth (kbps)')
    axes[1].plot([100, 100], [101, 101], color='red', label='Delay (ms)', linewidth=2.5)
    # axes[1].set_title(f"(b) 0.04x")
    # axes[1].set_ylabel("Frame Size (kbps)")
    axes[1].grid(True, linestyle='--', alpha=0.7)
    ax1_right = axes[1].twinx()
    ax1_right.plot(frame_index[start_index:end_index], delay04[start_index:end_index], 'r', linewidth=2.5, label='Delay (ms)')
    ax1_right.set_ylim(0, 360)
    axes[1].legend(loc='upper right')

    axes[2].plot(frame_index[start_index:end_index], frame_sizes_adaptive[start_index:end_index], 'b', linewidth=2.5, label='Frame Size (kbps)')
    axes[2].plot(frame_index[start_index:end_index], bitrates[start_index:end_index], 'black', linewidth=2.5, linestyle='--', label='Network Bandwidth (kbps)')
    # axes[2].plot(frame_index[100:110], frame_sizes_adaptive[100:110], 'b', linewidth=4)
    # axes[2].set_title(f"(c) adaptive")
    # axes[2].set_ylabel("Frame Size (kbps)")
    ax2_right = axes[2].twinx()
    ax2_right.plot(frame_index[start_index:end_index], delay_adaptive[start_index:end_index], 'r', linewidth=2.5, label='Delay (ms)')
    ax2_right.set_ylabel("Delay (ms)", fontsize=22, color='red')
    ax2_right.tick_params(axis="y", labelcolor='red')
    ax2_right.set_ylim(0, 360)
    axes[2].grid(True, linestyle='--', alpha=0.7)

    # fig.text(0.5, 0.05, 'Frame Index', ha='center', va='center', fontsize=fontsize)
    
    fontsize = 22
    fig.text(0.22, 0.05, f"(a) 0.5x", ha='center', fontsize=fontsize)
    fig.text(0.54, 0.05, f"(b) 0.04x", ha='center', fontsize=fontsize)
    fig.text(0.83, 0.05, f"(c) adaptive", ha='center', fontsize=fontsize)
  
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.2)
    
    output_file = f'10to1_frame_size.png'
    plt.savefig(output_file)
    plt.close()

def DrawFrameSizeCompare(output_dir_prefix, bitrate_indexes, network_bandwidths, start_index, end_index, output_file_name):
    original_dir = f'{output_dir_prefix}_0/'
    adaptive_dir = f'{output_dir_prefix}_adaptive_0/'
    original_frame_sizes = ExtractFrameSize(original_dir)
    adaptive_frame_sizes = ExtractFrameSize(adaptive_dir)
    frame_index = list(range(len(original_frame_sizes)))
    bitrates = GenerateBitratePoint(bitrate_indexes, network_bandwidths, len(original_frame_sizes))
    if end_index > len(original_frame_sizes):
        end_index = len(original_frame_sizes)
    
    plt.figure(figsize=(5,4))
    plt.plot(frame_index[start_index:end_index], original_frame_sizes[start_index:end_index], label='originalFrame Size', color='blue')
    plt.plot(frame_index[start_index:end_index], adaptive_frame_sizes[start_index:end_index], label='originalFrame Size', color='green')
    plt.plot(frame_index[start_index:end_index], bitrates[start_index:end_index], label='Network Bandwidth', color='red')
    plt.xlabel('Frame Index')
    plt.ylabel('Frame Size (kbps)')
    plt.legend()
    plt.grid()
    output_file = f'{output_dir_prefix}_0/{output_file_name}.png'
    plt.savefig(output_file)
    plt.close()


if __name__ == "__main__":
    data = 'Lecture_1080p'
    datas = ['Game_scene_change', 'ReadySteadyGo', 'Lecture1080p', 'Game_gray']# 'Game_scene_change']#, 'Game_minecraft', 'Game_screen', 'Game_shoot', 'Game_shoot_static', 'ReadySteadyGo', 'static']
    bitrates = ['static_10mbps', 'static_5mbps', 'static_2mbps', 'static_1mbps']
    bitrates = ['static_2mbps']
    bitrate_category_lists = ['0.04', '0.06', '0.08', '0.1', '0.3', '0.5', '0.7', '1.0']#, 'adaptive']
    speeds = [1, 2, 4, 8]
    bitrate_category_lists = ['0.3']
    speeds = [8]
    
    DrawThreeSubplots(f'result/{data}/10to1/')
    exit(0)

    for data in datas:
        for speed in speeds:
            data_file = data
            if speed > 1:
                data_file = f'{data}_{speed}x'
            for bitrate in bitrates:
                bitrate_file = f'input/bitrate_config/{bitrate}'
                bitrate_indexes = []
                network_bandwidths = []
                read_data_from_file(bitrate_file, 2, [bitrate_indexes, network_bandwidths], ',')
                # if len(bitrate_indexes) < 2 or len(network_bandwidths) < 2:
                #     print(f'Error: {bitrate_file} is not valid')
                #     continue
                bitrate_indexes = [int(x) for x in bitrate_indexes]
                network_bandwidths = [int(x) for x in network_bandwidths]
                for bitrate_category in bitrate_category_lists:
                    result_dir = f'result/{data_file}/{bitrate}/{bitrate_category}_20/'
                    print(result_dir, bitrate_indexes, network_bandwidths)
                    DrawFrameSize(result_dir, bitrate_indexes, network_bandwidths, bitrate_category, 1)#, 60, 150)
                    # DrawDelay(result_dir, bitrate_indexes, network_bandwidths, bitrate_category, 1)
                    # DrawVmaf(result_dir, bitrate_indexes, network_bandwidths, bitrate_category)
                    # DrawPSNR(result_dir, bitrate_indexes, network_bandwidths, bitrate_category)

                    # result_dir = f'result/{data}/{bitrate}/{bitrate_category}_adaptive_0/'
                    # DrawFrameSize(result_dir, bitrate_indexes, network_bandwidths)

                    # result_dir_prefix = f'result/{data}/{bitrate}/{bitrate_category}'
                    # DrawFrameSizeCompare(result_dir_prefix, bitrate_indexes, network_bandwidths, 0, 1000, 'frame_size_compare')
                    # DrawFrameSizeCompare(result_dir_prefix, bitrate_indexes, network_bandwidths, 80, 130, 'frame_size_compare_drop_period')
                    exit(0)