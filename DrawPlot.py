import csv

import matplotlib.pyplot as plt
import numpy as np
import statistics
from pathlib import Path

def DrawDelayPlot(file_prefix, label, result_path, file_name, bitrate_config):
    # Read data from a CSV file
    with open(f"{file_prefix}{label}.csv", 'r') as file:
        next(file)
        reader = csv.reader(file, delimiter=',')
        data = list(reader)

    start_index = 0
    end_index = data.__len__()
    # start_index = 100
    # end_index = 180
    # Extract the data
    frame_index = [float(row[0]) for row in data][start_index:end_index]
    frame_receive_delay = [float(row[6]) for row in data][start_index:end_index]
    frame_display_delay = [float(row[7]) for row in data][start_index:end_index]

    print(f"{file_name}, {bitrate_config}, {label} Average receive delay value is {statistics.mean(frame_receive_delay)} ms")
    print(f"{file_name}, {bitrate_config}, {label} Average display delay value of {statistics.mean(frame_display_delay)} ms")
    with open(result_path,'a') as fd:
        fd.write(f"{file_name}, {bitrate_config}, {statistics.mean(frame_receive_delay)}, {statistics.mean(frame_display_delay)},")

    plt.plot(frame_index, frame_receive_delay, label = f"{file_name} {bitrate_config} {label} receive delay", linewidth = '1')  # Plot the chart
    plt.plot(frame_index, frame_display_delay, label = f"{file_name} {bitrate_config} {label} display delay", linewidth = '1')  # Plot the chart

def DrawFrameSizePlot(file_prefix, label, draw_bitrate = False):
    # Read data from a CSV file
    with open(f"{file_prefix}{label}.csv", 'r') as file:
        next(file)
        reader = csv.reader(file, delimiter=',')
        data = list(reader)

    start_index = 0
    end_index = data.__len__()
    # start_index = 100
    # end_index = 180
    # Extract the data
    frame_size = [float(row[1]) for row in data][start_index:end_index]

    time = np.arange(frame_size.__len__())

    if draw_bitrate:
        bitrate = [float(row[0]) for row in data][start_index:end_index]
        plt.plot(time, bitrate, label = "bitrate", linewidth = '1')

    if label == 'default_drop':
        plt.plot(time, frame_size, label = label, linewidth = '1')  # Plot the chart
    else:
        plt.plot(time, frame_size, label = label, linewidth = '1')

def main():
    file_names = ["Lecture720", "Lecture1", "Lecture2", "Lecture3", "Lecture4", "Sports", "Sport2", "Animation1", "Animation2", "CoverSong", "Gaming"]
    bitrate_configs = ["static", "3000-1500", "3000-300", "3000-50"]
    project_path = "/Users/menghua/Research/TestX264/"
    result_path = f"{project_path}delay_statistics.csv"

    draw_frame_size = False
    draw_delay = True
    if (Path(result_path).exists()):
        Path(result_path).unlink()

    for file_name in file_names:
        for bitrate_config in bitrate_configs:
            plt.figure(figsize=(14,6))
            file_prefix = f"{project_path}result/{file_name}_{bitrate_config}/"

            # Draw frame size plot
            if draw_frame_size:
                DrawFrameSizePlot(file_prefix, "default", True)
                DrawFrameSizePlot(file_prefix, "opt")
                plt.legend()
                plt.savefig(f"{project_path}result_plots/FrameSize/{file_name}_{bitrate_config}.png")
                # plt.show()  # display
                plt.close()

            # Draw delay plot
            if draw_delay:
                DrawDelayPlot(file_prefix, f"default_delay_statistics", result_path, file_name, bitrate_config)
                DrawDelayPlot(file_prefix, f"opt_delay_statistics", result_path, file_name, bitrate_config)
                with open(result_path,'a') as fd:
                    fd.write("\n")
                plt.legend()
                # plt.savefig(f"{project_path}result_plots/Delay/{file_name}_{bitrate_config}.png")
                # plt.show()  # display
                plt.close()

if __name__ == "__main__": 
    main() 