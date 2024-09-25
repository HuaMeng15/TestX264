from math import log10, sqrt
from pathlib import Path
import cv2
import csv
import ffmpeg
import numpy as np
import matplotlib.pyplot as plt
import statistics
  
def PSNR(original, compressed): 
    mse = np.mean((original - compressed) ** 2) 
    if(mse == 0):  # MSE is zero means no noise is present in the signal . 
                  # Therefore PSNR have no importance. 
        return 100
    max_pixel = 255.0
    psnr = 20 * log10(max_pixel / sqrt(mse)) 
    return psnr

def CalcAndSavePSNR(result_path, file_suffix, input_frames_directory):
    psnr = []
    frames_directory = f"{result_path}comparison_{file_suffix}/"
    render_frame_index_path = f"{result_path}{file_suffix}_render_frame.txt"
    psnr_file = f"{result_path}{file_suffix}_psnr.csv"

    with open(render_frame_index_path, 'r') as file:
        reader = csv.reader(file, delimiter=',')
        data = list(reader)
 
    render_frame_index = [int(row[1]) for row in data]

    if (not Path(frames_directory).exists()):
        video_path = f"{result_path}{file_suffix}.mkv"
        Path(frames_directory).mkdir(parents=True, exist_ok=True)
        (
            ffmpeg.input(video_path)
            .output(f"{frames_directory}output_%04d.png")
            .run()
        )

    if (not Path(psnr_file).exists()):
        with open(psnr_file, 'w') as file:
            writer = csv.writer(file)
            for i in range(1, render_frame_index.__len__()):
                original = cv2.imread(f"{input_frames_directory}input_{i:04d}.png") 
                compressed = cv2.imread(f"{frames_directory}output_{(render_frame_index[i - 1] + 1):04d}.png", 1)
                value = PSNR(original, compressed)
                psnr.append(value)
                writer.writerow([i, value])
            file.close()
    else:
        with open(psnr_file, 'r') as file:
            reader = csv.reader(file, delimiter=',')
            data = list(reader)
        psnr = [float(row[1]) for row in data]
    
    start_index = 0
    end_index = psnr.__len__()
    print(f"{file_suffix} Average PSNR value is {statistics.mean(psnr)} dB")
    print(f"{file_suffix} Average PSNR value of {start_index} - {end_index} is {statistics.mean(psnr[start_index:end_index])} dB")
    time = np.arange(psnr.__len__())
    if file_suffix == 'default_no_drop':
        plt.plot(time[start_index:end_index], psnr[start_index:end_index], label = file_suffix, linewidth = '1')  # Plot the chart
    else:
        plt.plot(time[start_index:end_index], psnr[start_index:end_index], label = file_suffix, linewidth = '1')  # Plot the chart

def main():
    project_path = "/Users/menghua/Research/TestX264/"
    file_name = "Lecture1"
    bitrate_config = "3000-50"
    input_frames_directory = f"{project_path}input/{file_name}_input_frames/"
    result_path = f"{project_path}result/{file_name}_{bitrate_config}/"
    save_fig_path = f"{project_path}result_plots/PSNR/PSNR_{file_name}_{bitrate_config}.png"

    default_drop = 'default_drop'
    default_no_drop = 'default_no_drop'
    opt_drop = 'opt_drop'
    opt_no_drop = 'opt_no_drop'

    plt.figure(figsize=(14,6))
    CalcAndSavePSNR(result_path, default_no_drop, input_frames_directory)
    CalcAndSavePSNR(result_path, default_drop, input_frames_directory)
    CalcAndSavePSNR(result_path, opt_no_drop, input_frames_directory)
    CalcAndSavePSNR(result_path, opt_drop, input_frames_directory)
    # CalcAndSavePSNR(result_path, "default", input_frames_directory)
    # CalcAndSavePSNR(result_path, "opt", input_frames_directory)

    plt.legend()
    # plt.savefig(save_fig_path)
    plt.show()  # display
       
if __name__ == "__main__": 
    main() 