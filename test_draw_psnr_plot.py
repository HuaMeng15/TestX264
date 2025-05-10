import cv2
import numpy as np
from math import log10, sqrt
import os
import matplotlib.pyplot as plt

def calc_psnr(path1, path2):
    image1 = cv2.imread(path1)
    image2 = cv2.imread(path2)
    mse = np.mean((image1 - image2) ** 2)
    if(mse == 0):  # MSE is zero means no noise is present in the signal .
                  # Therefore PSNR have no importance.
        return 100
    max_pixel = 255.0
    psnr = 20 * log10(max_pixel / sqrt(mse))
    return psnr

if __name__ == "__main__":
    change_index = 190
    send_dir = 'test_raw_frames_send/'
    original_dir = 'test_raw_frames_original/'
    test_dir = 'test_raw_frames_' + str(change_index) + '/'
    frame_count = 576
    original_psnr_list = []
    new_psnr_list = []

    for i in range(576):
        send_frame = send_dir + 'frame' + str(i + 1) + '.png'
        original_frame = original_dir + 'frame' + str(i + 1) + '.png'
        compare_frame = test_dir + 'frame' + str(i + 1) + '.png'
        original_psnr = calc_psnr(send_frame, original_frame)
        new_psnr = calc_psnr(send_frame, compare_frame)
        original_psnr_list.append(original_psnr)
        new_psnr_list.append(new_psnr)

    plt.grid()
    plt.plot(range(len(original_psnr_list)), original_psnr_list, label='Original PSNR')
    plt.plot(range(len(new_psnr_list)), new_psnr_list, label='New PSNR')
    plt.xlabel('Frame Number')
    plt.ylabel('PSNR')
    plt.legend()
    fig_path = 'psnr_plot_' + str(change_index) + '.png'
    plt.savefig(fig_path)
    plt.close()
