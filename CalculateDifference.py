import cv2
import numpy as np
import os
from PIL import Image
import matplotlib.pyplot as plt

def calculate_mse(image1_path, image2_path):
    # Load the images
    image1 = Image.open(image1_path)
    image2 = Image.open(image2_path)

    # Convert images to numpy arrays
    array1 = np.array(image1)
    array2 = np.array(image2)

    # Check if the dimensions match
    if array1.shape != array2.shape:
        raise ValueError("Images must have the same dimensions.")

    # Calculate the Mean Squared Error
    mse = np.mean((array1 - array2) ** 2)
    return mse

def draw_plot(mse_list, output_fig):
    size = len(mse_list)#min(len(mse_list), len(ssim_list))
    index = list(range(size))

    plt.figure(figsize = (5, 4))
    plt.rcParams['font.size'] = 14
    plt.xlabel('index')
    plt.ylabel('mse')
    plt.plot(index, mse_list)
    plt.grid()
    plt.tight_layout()
    plt.savefig(output_fig)

def read_data_from_file(file, count, data_lists, seperator):
    lines = open(file,'r').read().split('\n')
    for line in lines:
        line = line.split(seperator)
        if len(line) < count:
            continue
        for i in range(count):
            data_lists[i].append(line[i])

if __name__ == "__main__":
    datas = ['Game_gray', 'Lecture1080p', 'Game_minecraft', 'Game_scene_change', 'Game_screen', 'Game_shoot', 'Game_shoot_static', 'ReadySteadyGo', 'static']
    datas = ['Game_screen_part']#'Game_gray', 'Lecture1080p', 'ReadySteadyGo']
    speeds = [1, 2, 4, 8]
    
    for data in datas:
        for speed in speeds:
            # speed = 8
            raw_frame_dir = f'input/{data}_raw_frames/'

            frame_count = len(os.listdir(raw_frame_dir))
            output_file = f"difference/{data}_{speed}x_mse.log"
            output_file = f"difference/{data}_mse.log"
            mse_list = []
            frame_count = int(frame_count / speed)
            
            # start_index = 500
            # end_index = start_index + 100
            
            # read_data_from_file(output_file, 1, [mse_list], '\n')
            # mse_list = [float(x) for x in mse_list if x]
            print(f"Processing {data} with {frame_count} frames...")

            for i in range(frame_count):
                frame1 = raw_frame_dir + str(1 + i * speed) + ".png"
                frame2 = raw_frame_dir + str(1 + (i + 1) * speed) + ".png"
                if not os.path.exists(frame1) or not os.path.exists(frame2):
                    print(f"Frames {frame1} or {frame2} do not exist, skipping...")
                    continue
                mse = calculate_mse(frame1, frame2)
                print(f"Frame {i + 1} vs Frame {i + 2}: MSE = {mse}")
                mse_list.append(mse)
            
            # draw_plot(mse_list[start_index:end_index], f'difference/{data}_{speed}x_SATD_{start_index}:{end_index}.png')
            draw_plot(mse_list, f'difference/{data}.png')
            
            # mse_list = []
            # read_data_from_file(f"difference/{data}_{speed}x_mse.log", 1, [mse_list], '\n')
            # mse_list = [float(x) for x in mse_list if x]
            # print(f"Processing {data} with {frame_count} frames...")
            # draw_plot(mse_list[start_index:end_index], f'difference/{data}_{speed}x_MSE_{start_index}:{end_index}.png')
            # exit(0)

            with open(output_file, 'w') as f_file:
                for mse in mse_list:
                    f_file.write(str(mse) + "\n")
            exit(0)