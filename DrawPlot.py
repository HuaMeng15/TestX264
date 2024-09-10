import csv

import matplotlib.pyplot as plt
import numpy as np

# Read data from a CSV file
with open('/Users/menghua/Research/TestX264/result/statistics_with_bitrate_buffer_with_smooth.csv', 'r') as file:
    reader = csv.reader(file, delimiter=',')
    data = list(reader)

# Extract the data
bitrate = [float(row[0]) for row in data]
frame_size = [float(row[1]) for row in data]

time = np.arange(data.__len__())

plt.plot(time, bitrate, label = "bitrate")  # Plot the chart
plt.plot(time, frame_size, label = "frame_size")
plt.legend()
plt.show()  # display