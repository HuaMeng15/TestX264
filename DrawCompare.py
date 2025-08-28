import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np
import os

def read_data_from_file(file, count, data_lists, seperator):
    lines = open(file,'r').read().split('\n')
    for line in lines:
        line = line.split(seperator)
        if len(line) < count or line[0] == '':
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
    for i in range(len(frame_sizes)):
        if frame_sizes[i] <= 0:
            frame_sizes[i] = frame_sizes[i - 1]
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

def DrawMultipleMetrics(output_dir, bitrate_indexes, network_bandwidths, bitrate_category, qp_step, output_file_name, data_file_name, start_index=0, end_index=10000):
    frame_sizes = ExtractFrameSize(output_dir)
    bitrates = GenerateBitratePoint(bitrate_indexes, network_bandwidths, len(frame_sizes))
    bitrates = bitrates[start_index:end_index]
    frame_sizes = frame_sizes[start_index:end_index]
    frame_index = list(range(start_index + 1, len(frame_sizes) + start_index + 1))
    
    delay = ExtractDelay(output_dir)[start_index - 1:end_index - 1]
    
    for i in range(len(delay)):
        if delay[i] <= 0:
            delay[i] = delay[i - 1]
    
    vmaf = ExtractVmaf(output_dir)[start_index - 1:end_index - 1]
    psnr = []
    psnr_file = f'{output_dir}psnr_score.log'
    read_data_from_file(psnr_file, 2, [[], psnr], ',')
    psnr = [float(x) for x in psnr][start_index - 1:end_index - 1]
    
    qp = []
    qp_file = f'{output_dir}qp.log'
    read_data_from_file(qp_file, 2, [[], qp], ',')
    qp = [float(x) for x in qp][start_index:end_index]
    
    print(frame_sizes[0], qp[0])
    
    global_qp_file = f'global_qp_{qp_step}.log'
    if os.path.exists(global_qp_file):
        global_qp = []
        read_data_from_file(global_qp_file, 1, [global_qp], ',')
        global_qp = [float(x) for x in global_qp][start_index:end_index]
    
    difference_file = f'difference/{data_file_name}_mse.log'
    differences = []
    read_data_from_file(difference_file, 1, [differences], ',')
    differences = differences[start_index - 1:end_index - 1]
    differences = [float(x) for x in differences]
    differences = differences[:len(frame_index)]
    
    # mse_file = f'difference/{data_file_name}_mse3.log'
    # mses = []
    # read_data_from_file(mse_file, 1, [mses], ',')
    # mses = mses[start_index - 1:end_index - 1]
    # mses = [float(x) for x in mses]
    # mses = mses[:len(frame_index)]
    
    # complexity_file = f'difference/{data_file_name}_complexity.log'
    # complexities = []
    # read_data_from_file(complexity_file, 1, [complexities], ',')
    # complexities = complexities[start_index - 1:end_index - 1]
    # complexities = [float(x) for x in complexities]
    # complexities = complexities[:len(frame_index)]
    
    if len(differences) != len(frame_sizes) or len(frame_sizes) != len(frame_index) or\
        len(delay) != len(frame_index) or len(vmaf) != len(frame_index) or len(bitrates) != len(frame_index):
        print(f'Error: input file is not valid length: {len(differences)}, {len(frame_sizes)}, {len(frame_index)}, {len(delay)}, {len(vmaf)}, {len(bitrates)}')
        return
    
    # plt.figure(figsize=(26,8))
    plt.rcParams['font.size'] = 20

    fig, ax1 = plt.subplots(figsize=(16, 8))

    # Plot frame size
    ax1.set_xlabel('Frame Index')
    ax1.set_ylabel('Frame Size(kbps)', color='tab:blue')
    # ax1.set_ylim(0, 4500)
    ax1.plot(frame_index, frame_sizes, color='tab:blue', label='Frame Size')
    ax1.plot(frame_index, bitrates, color='black', linestyle='--', label='Network Bandwidth')
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    
    # ax1.set_ylabel('global QP', color='tab:blue')
    # ax1.plot(frame_index, global_qp, color='tab:blue', label='global QP')
    # ax1.tick_params(axis='y', labelcolor='tab:blue')

    # Create a second y-axis for MSE
    ax2 = ax1.twinx()
    ax2.set_ylabel('MSE', color='tab:orange')
    ax2.plot(frame_index, differences, color='tab:orange', label='MSE', alpha=0.3)
    ax2.tick_params(axis='y', labelcolor='tab:orange')

    # Create a third y-axis for VMAF
    use_psnr = 1
    use_psnr = 0
    if use_psnr:
        ax3 = ax1.twinx()
        ax3.spines['right'].set_position(('outward', 60))  # Offset the third y-axis
        ax3.set_ylabel('PSNR', color='tab:green')
        ax3.plot(frame_index, psnr, color='tab:green', label='PSNR')
        ax3.tick_params(axis='y', labelcolor='tab:green')
    else:
        ax3 = ax1.twinx()
        ax3.spines['right'].set_position(('outward', 60))  # Offset the third y-axis
        ax3.set_ylabel('VMAF', color='tab:green')
        # ax3.set_ylim(84, 99)
        ax3.plot(frame_index, vmaf, color='tab:green', label='VMAF', alpha=0.5)
        ax3.tick_params(axis='y', labelcolor='tab:green')

    # Create a fourth y-axis for delay
    ax4 = ax1.twinx()
    ax4.spines['right'].set_position(('outward', 120))  # Offset the fourth y-axis
    ax4.set_ylabel('Delay', color='tab:red')
    # ax4.set_ylim(0, 72)
    ax4.plot(frame_index, delay, color='tab:red', label='Delay', alpha=0.5)
    ax4.tick_params(axis='y', labelcolor='tab:red')
    
    ax5 = ax1.twinx()
    ax5.spines['right'].set_position(('outward', 180))  #
    ax5.set_ylabel('QP', color='tab:purple')
    # ax5.set_ylim(11, 30)
    ax5.plot(frame_index, qp, color='tab:purple', label='QP')
    ax5.scatter(frame_index, qp, color='tab:purple', s=10)  # Scatter plot for QP
    # for i in range(20, 25):
    #     ax5.annotate(f'{qp[i]}', (frame_index[i], qp[i]), textcoords="offset points", xytext=(5,0), ha='left', va='center', fontsize=13)
    ax5.tick_params(axis='y', labelcolor='tab:purple')
    
    # Add grid and subgrid
    ax1.grid(True, which='both', linestyle='--', linewidth=1)  # Major grid
    ax1.minorticks_on()  # Enable minor ticks
    ax1.grid(True, which='minor', linestyle=':', linewidth=1)  # Minor grid

    # Show the plot
    fig.tight_layout()  # To ensure the layout is nice

    output_file = f'{output_file_name}.png'
    plt.savefig(output_file)
    plt.close()

if __name__ == "__main__":
    datas = ['Game_gray', 'Lecture1080p', 'ReadySteadyGo', 'Game_scene_change']#, 'Game_minecraft', 'Game_screen', 'Game_shoot', 'Game_shoot_static', 'ReadySteadyGo', 'static']
    bitrates = ['static_10mbps', 'static_5mbps', 'static_2mbps', 'static_1mbps']
    bitrates = ['static_2mbps']
    bitrate_category_lists = ['0.04', '0.06', '0.08', '0.1', '0.3', '0.5', '0.7', '1.0']#, 'adaptive']
    speeds = [1, 2, 4, 8]
    bitrate_category_lists = ['0.3']#, 'adaptive']#'0.3', '0.04', '0.7']#'test']
    qp_steps = [1, 2, 4, 8, 10, 20]
    qp_steps = [4, 10]
    speeds = [1]
    
    # DrawThreeSubplots(f'result/{data}/10to1/')
    # exit(0)
    
    start_index = 3
    end_index = 10000
    start_index = 150
    # end_index = start_index + 100

    for data in datas:
        data = 'Game_screen_part'
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
                    for qp_step in qp_steps:
                        result_dir = f'result/{data_file}/{bitrate}/{bitrate_category}_{qp_step}/'
                        print(result_dir, bitrate_indexes, network_bandwidths)
                        DrawMultipleMetrics(result_dir, bitrate_indexes, network_bandwidths, bitrate_category, qp_step, f'qp_compre_{data_file}_{bitrate}_{bitrate_category}_{qp_step}_{start_index}_{end_index}', data_file, start_index, end_index)
                        # exit(0)
        exit(0)