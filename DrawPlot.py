import csv

import matplotlib.pyplot as plt
import numpy as np

def DrawPlot(file_prefix, label, draw_bitrate = False):
    # Read data from a CSV file
    with open(f"{file_prefix}{label}.csv", 'r') as file:
        reader = csv.reader(file, delimiter=',')
        data = list(reader)

    # start_index = 0
    # end_index = data.__len__()
    start_index = 100
    end_index = 180
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
    file_name = "Lecture4"
    bitrate_config = "3000-50"
    project_path = "/Users/menghua/Research/TestX264/"
    file_prefix = f"{project_path}result/{file_name}_{bitrate_config}/"
    default_drop = 'default_drop'
    default_no_drop = 'default_no_drop'
    opt_drop = 'opt_drop'
    opt_no_drop = 'opt_no_drop'

    plt.figure(figsize=(14,6))
    DrawPlot(file_prefix, default_drop, True)
    DrawPlot(file_prefix, default_no_drop)
    DrawPlot(file_prefix, opt_drop)
    DrawPlot(file_prefix, opt_no_drop)
    # DrawPlot(file_prefix, "default", True)
    # DrawPlot(file_prefix, "opt")

    plt.legend()
    plt.savefig(f"{project_path}result_plots/FrameSize/FrameSize_{file_name}_{bitrate_config}.png")
    # plt.show()  # display

if __name__ == "__main__": 
    main() 