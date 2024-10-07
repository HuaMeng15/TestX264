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

def CalcAndSavePSNR(result_path, file_suffix, input_frames_directory, psnr_statistics_path, file_name, bitrate_config, enable_drop_frame):
    psnr = []
    display_psnr = []
    frames_directory = f"{result_path}comparison_{file_suffix}/"
    render_frame_index_path = f"{result_path}{file_suffix}_render_frame.txt"
    delay_file = f"{result_path}{file_suffix}_delay_statistics.csv"
    psnr_file = f"{result_path}{file_suffix}_psnr.csv"
    display_psnr_file = f"{result_path}{file_suffix}_display_psnr.csv"

    with open(render_frame_index_path, 'r') as file:
        reader = csv.reader(file, delimiter=',')
        data = list(reader)

    render_frame_index = [int(row[1]) for row in data]

    with open(delay_file, 'r') as file:
        next(file)
        reader = csv.reader(file, delimiter=',')
        data = list(reader)

    send_frame_index_when_display = [float(row[2]) for row in data]

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
                if enable_drop_frame:
                    compressed = cv2.imread(f"{frames_directory}output_{(render_frame_index[i - 1] + 1):04d}.png", 1)
                else:
                    compressed = cv2.imread(f"{frames_directory}output_{i:04d}.png", 1)
                value = PSNR(original, compressed)
                psnr.append(value)
                writer.writerow([i, value])
            file.close()
    else:
        with open(psnr_file, 'r') as file:
            reader = csv.reader(file, delimiter=',')
            data = list(reader)
        psnr = [float(row[1]) for row in data]

    frame_size = send_frame_index_when_display.__len__()
    if (not Path(display_psnr_file).exists()):
        with open(display_psnr_file, 'w') as file:
            writer = csv.writer(file)
            for i in range(0, render_frame_index.__len__() - 1):
                original_index = int(send_frame_index_when_display[i]) + 1
                if original_index >= frame_size:
                    original_index = frame_size

                original = cv2.imread(f"{input_frames_directory}input_{original_index:04d}.png")
                compressed = cv2.imread(f"{frames_directory}output_{i + 1:04d}.png", 1)
                value = PSNR(original, compressed)
                display_psnr.append(value)
                writer.writerow([i, value])
            file.close()
    else:
        with open(display_psnr_file, 'r') as file:
            reader = csv.reader(file, delimiter=',')
            data = list(reader)
        display_psnr = [float(row[1]) for row in data]

    
    start_index = 0
    end_index = psnr.__len__()
    print(f"{file_suffix} Average PSNR value is {statistics.mean(psnr)} dB")
    # print(f"{file_suffix} Average PSNR value of {start_index} - {end_index} is {statistics.mean(psnr[100:180])} dB")
    print(f"{file_suffix} Average display_psnr value is {statistics.mean(display_psnr)} dB")

    with open(psnr_statistics_path,'a') as fd:
        fd.write(f"{file_name}, {bitrate_config}, {statistics.mean(psnr)}, {statistics.mean(display_psnr)},")
    time = np.arange(psnr.__len__())
    if file_suffix == 'default_no_drop':
        plt.plot(time[start_index:end_index], psnr[start_index:end_index], label = file_suffix, linewidth = '1')  # Plot the chart
    else:
        plt.plot(time[start_index:end_index], psnr[start_index:end_index], label = file_suffix, linewidth = '1')  # Plot the chart

def main():
    file_names = ["Lecture720", "Lecture1", "Lecture2", "Lecture3", "Lecture4", "Sports", "Sport2", "Animation1", "Animation2", "CoverSong", "Gaming"]
    bitrate_configs = ["static", "3000-1500", "3000-300", "3000-50"]
    project_path = "/Users/menghua/Research/TestX264/"
    psnr_statistics_path = f"{project_path}psnr_statistics.csv"

    if (Path(psnr_statistics_path).exists()):
        Path(psnr_statistics_path).unlink()

    for file_name in file_names:
        input_frames_directory = f"{project_path}input/{file_name}_input_frames/"
        for bitrate_config in bitrate_configs:
            result_path = f"{project_path}result/{file_name}_{bitrate_config}/"
            plt.figure(figsize=(14,6))
            CalcAndSavePSNR(result_path, "default", input_frames_directory, psnr_statistics_path, file_name, bitrate_config, False)
            CalcAndSavePSNR(result_path, "opt", input_frames_directory, psnr_statistics_path, file_name, bitrate_config, False)
            with open(psnr_statistics_path,'a') as fd:
                fd.write("\n")
            plt.legend()
            plt.savefig(f"{project_path}result_plots/PSNR/{file_name}_{bitrate_config}.png")
            # plt.show()  # display
            plt.close()
       
if __name__ == "__main__": 
    main() 