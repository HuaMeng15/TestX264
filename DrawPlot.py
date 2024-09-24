import csv

import matplotlib.pyplot as plt
import numpy as np

def DrawPlot(file_prefix, label, draw_bitrate = False):
    # Read data from a CSV file
    with open(f"{file_prefix}{label}.csv", 'r') as file:
        reader = csv.reader(file, delimiter=',')
        data = list(reader)

    # Extract the data
    frame_size = [float(row[1]) for row in data][100:200]

    time = np.arange(frame_size.__len__())

    if draw_bitrate:
        bitrate = [float(row[0]) for row in data][100:200]
        plt.plot(time, bitrate, label = "bitrate", linewidth = '1')

    if label == 'default_drop':
        plt.plot(time, frame_size, label = label, linewidth = '1')  # Plot the chart
    else:
        plt.plot(time, frame_size, label = label, linewidth = '1')

def main():
    file_prefix = '/Users/menghua/Research/TestX264/result/lecture720_config3/'
    default_drop = 'default_drop'
    default_no_drop = 'default_no_drop'
    opt_drop = 'opt_drop'
    opt_no_drop = 'opt_no_drop'

    plt.figure(figsize=(14,6))
    DrawPlot(file_prefix, default_drop, True)
    DrawPlot(file_prefix, default_no_drop)
    DrawPlot(file_prefix, opt_drop)
    DrawPlot(file_prefix, opt_no_drop)

    plt.legend()
    plt.show()  # display

if __name__ == "__main__": 
    main() 