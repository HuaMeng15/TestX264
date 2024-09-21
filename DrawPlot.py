import csv

import matplotlib.pyplot as plt
import numpy as np

# Read data from a CSV file
with open('/Users/menghua/Research/TestX264/result/test.csv', 'r') as file:
    reader = csv.reader(file, delimiter=',')
    data = list(reader)

with open('/Users/menghua/Research/TestX264/input/frame_size2.log', 'r') as file:
    sizes2 = file.read().splitlines()

with open('/Users/menghua/Research/TestX264/input/frame_size.log', 'r') as file:
    sizes = file.read().splitlines()

with open('/Users/menghua/Research/TestX264/input/frame_size3.log', 'r') as file:
    sizes3 = file.read().splitlines()

with open('/Users/menghua/Research/TestX264/input/frame_size4.log', 'r') as file:
    sizes4 = file.read().splitlines()

bitrate = [12500] * sizes.__len__()
frame_size = [float(x.split('=')[1]) for x in sizes]
frame_size2 = [float(x.split('=')[1]) for x in sizes2]
frame_size3 = [float(x.split('=')[1]) for x in sizes3]
frame_size4 = [float(x.split('=')[1]) for x in sizes4]

# # Extract the data
bitrate1 = [float(row[0]) for row in data]
frame_size1 = [float(row[1]) for row in data]

time = np.arange(sizes.__len__())
time1 = np.arange(data.__len__())

plt.plot(time1, bitrate1, label = "bitrate")  # Plot the chart
plt.plot(time1, frame_size1, label = "frame_size")
plt.legend()
plt.show()  # display

# plt.plot(time, bitrate, label = "bitrate")  # Plot the chart
# # plt.plot(time, frame_size, label = "frame_size")
# # plt.plot(time, frame_size2, label = "frame_size2")
# plt.plot(time, frame_size3, label = "frame_size3")
# plt.plot(time, frame_size4, label = "frame_size4")
# plt.legend()
# plt.show()  # display